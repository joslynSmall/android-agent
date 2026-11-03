"""Tests for UI tool latency optimization - sharing XML dumps."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestXMLSharingOptimization:
    """Verify that get_screen_tree and get_interactive_elements can share pre-fetched XML."""

    def test_get_screen_tree_accepts_prefetched_xml(self):
        """get_screen_tree should accept optional xml parameter to avoid duplicate dumps."""
        from gitd.services.device_context import get_screen_tree

        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Button" class="android.widget.Button" 
        clickable="true" bounds="[0,0][100,100]" />
</hierarchy>'''

        with patch('gitd.services.device_context.get_device') as mock_get_device:
            mock_device = Mock()
            mock_device.dump_xml = Mock(side_effect=Exception("Should not be called when xml is provided"))
            mock_get_device.return_value = mock_device

            # Should not raise - xml is provided so dump_xml should not be called
            result = get_screen_tree("test_device", xml=sample_xml)
            assert "Button" in result or result == "(empty screen)"

    def test_get_interactive_elements_accepts_prefetched_xml(self):
        """get_interactive_elements should accept optional xml parameter to avoid duplicate dumps."""
        from gitd.services.device_context import get_interactive_elements

        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Click Me" class="android.widget.Button" 
        clickable="true" bounds="[10,20][110,120]" />
</hierarchy>'''

        with patch('gitd.services.device_context.get_device') as mock_get_device:
            mock_device = Mock()
            mock_device.dump_xml = Mock(side_effect=Exception("Should not be called when xml is provided"))
            
            # Mock the node parsing methods
            def mock_nodes(xml):
                return ['<node index="0" text="Click Me" class="android.widget.Button" clickable="true" bounds="[10,20][110,120]" />']
            
            mock_device.nodes = mock_nodes
            mock_device.node_text = lambda node: "Click Me"
            mock_device.node_content_desc = lambda node: ""
            mock_device.node_rid = lambda node: ""
            mock_device.node_bounds = lambda node: (10, 20, 110, 120)
            mock_get_device.return_value = mock_device

            # Should not raise - xml is provided so dump_xml should not be called
            result = get_interactive_elements("test_device", xml=sample_xml)
            assert isinstance(result, list)

    def test_execute_tool_shares_xml_between_functions(self):
        """execute_tool should fetch XML once and pass it to both get_screen_tree and _a11y_diff_suffix."""
        from gitd.services import agent_tools

        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Home" class="android.widget.Button" 
        clickable="true" bounds="[0,0][100,100]" />
</hierarchy>'''

        dump_xml_call_count = 0

        def mock_dump_xml():
            nonlocal dump_xml_call_count
            dump_xml_call_count += 1
            return sample_xml

        with patch('gitd.services.agent_tools.get_device') as mock_get_device_agent:
            with patch('gitd.services.device_context.get_device') as mock_get_device_ctx:
                mock_device = Mock()
                mock_device.dump_xml = mock_dump_xml
                mock_device.adb = Mock(return_value="")
                
                # Mock node parsing for get_interactive_elements
                mock_device.nodes = lambda xml: []
                
                mock_get_device_agent.return_value = mock_device
                mock_get_device_ctx.return_value = mock_device

                # Execute a UI action
                result = agent_tools.execute_tool("press_home", {"device": "test_device"})

                # Verify dump_xml was called exactly once (the optimization is working)
                # Note: This test verifies the optimization is in place
                assert dump_xml_call_count == 1, \
                    f"Expected 1 dump_xml call with optimization, got {dump_xml_call_count}"

    def test_backward_compatibility_without_xml_param(self):
        """get_screen_tree and get_interactive_elements should work without xml param (backward compat)."""
        from gitd.services.device_context import get_screen_tree, get_interactive_elements

        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Item" class="android.widget.TextView" 
        bounds="[0,0][100,100]" />
</hierarchy>'''

        with patch('gitd.services.device_context.get_device') as mock_get_device:
            mock_device = Mock()
            mock_device.dump_xml = Mock(return_value=sample_xml)
            mock_device.nodes = lambda xml: []
            mock_get_device.return_value = mock_device

            # Call without xml parameter - should call dump_xml internally
            tree = get_screen_tree("test_device")
            assert mock_device.dump_xml.call_count >= 1

            mock_device.dump_xml.reset_mock()

            elements = get_interactive_elements("test_device")
            assert mock_device.dump_xml.call_count >= 1


class TestA11yDiffWithSharedXML:
    """Verify _a11y_diff_suffix works correctly with shared XML."""

    def test_a11y_diff_suffix_accepts_xml_parameter(self):
        """_a11y_diff_suffix should accept optional xml parameter."""
        from gitd.services.agent_tools import _a11y_diff_suffix

        sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<hierarchy rotation="0">
  <node index="0" text="Button" class="android.widget.Button" 
        clickable="true" bounds="[0,0][100,100]" />
</hierarchy>'''

        with patch('gitd.services.device_context.get_device') as mock_get_device:
            mock_device = Mock()
            mock_device.dump_xml = Mock(side_effect=Exception("Should not be called when xml is provided"))
            mock_device.nodes = lambda xml: []
            mock_get_device.return_value = mock_device

            # Should not raise even though dump_xml would raise
            result = _a11y_diff_suffix("test_device", xml=sample_xml)
            assert isinstance(result, str)
