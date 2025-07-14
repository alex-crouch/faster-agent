#!/usr/bin/env python3

"""
Test script for tool_choice functionality in SGLang
Tests: required, auto, and specific function choices in both streaming and non-streaming modes
"""

import openai


def setup_client():
    """Setup OpenAI client pointing to SGLang server"""
    client = openai.Client(base_url="http://192.168.194.33:30000/v1", api_key="xxxxxx")
    model_name = client.models.list().data[0].id
    return client, model_name


def get_test_tools():
    """Get the test tools for function calling"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "use this to get latest weather information for a city given its name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "name of the city to get weather for",
                        }
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pokemon_info",
                "description": "get detailed information about a pokemon given its name",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "name of the pokemon to get info for",
                        }
                    },
                    "required": ["name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "make_next_step_decision",
                "description": "You will be given a trace of thinking process in the following format.\n\nQuestion: the input question you must answer\nTOOL: think about what to do, and choose a tool to use ONLY IF there are defined tools. \n  You should never call the same tool with the same input twice in a row.\n  If the previous conversation history already contains the information that can be retrieved from the tool, you should not call the tool again.\nOBSERVATION: the result of the tool call, NEVER include this in your response, this information will be provided\n... (this TOOL/OBSERVATION can repeat N times)\nANSWER: If you know the answer to the original question, require for more information,\n  or you don't know the answer and there are no defined tools or all available tools are not helpful, respond with the answer without mentioning anything else.\n  If the previous conversation history already contains the answer, respond with the answer right away.\n\n  If no tools are configured, naturally mention this limitation while still being helpful. Briefly note that adding tools in the agent configuration would expand capabilities.\n\nYour task is to respond with the next step to take, based on the traces, \nor answer the question if you have enough information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "decision": {
                            "type": "string",
                            "description": 'The next step to take, it must be either "TOOL" or "ANSWER". If the previous conversation history already contains the information that can be retrieved from the tool, you should not call the tool again. If there are no defined tools, you should not return "TOOL" in your response.',
                        },
                        "content": {
                            "type": "string",
                            "description": 'The content of the next step. If the decision is "TOOL", this should be a short and concise reasoning of why you chose the tool, MUST include the tool name. If the decision is "ANSWER", this should be the answer to the question. If no tools are available, integrate this limitation conversationally without sounding scripted.',
                        },
                    },
                    "required": ["decision", "content"],
                },
            },
        },
    ]


def get_test_messages():
    """Get test messages that should trigger tool usage"""
    return [
        {
            "role": "user",
            "content": "Answer the following questions as best you can:\n\nYou will be given a trace of thinking process in the following format.\n\nQuestion: the input question you must answer\nTOOL: think about what to do, and choose a tool to use ONLY IF there are defined tools\nOBSERVATION: the result of the tool call or the observation of the current task, NEVER include this in your response, this information will be provided\n... (this TOOL/OBSERVATION can repeat N times)\nANSWER: If you know the answer to the original question, require for more information, \nif the previous conversation history already contains the answer, \nor you don't know the answer and there are no defined tools or all available tools are not helpful, respond with the answer without mentioning anything else.\nYou may use light Markdown formatting to improve clarity (e.g. lists, **bold**, *italics*), but keep it minimal and unobtrusive.\n\nYour task is to respond with the next step to take, based on the traces, \nor answer the question if you have enough information.\n\nQuestion: what is the weather in top 5 populated cities in the US?\n\nTraces:\n\n\nThese are some additional instructions that you should follow:",
        }
    ]


def get_travel_tools():
    """Get tools for travel assistant scenario that should trigger multiple tool calls"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a given location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The name of the city or location.",
                        },
                        "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                    },
                    "required": ["location", "unit"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_tourist_attractions",
                "description": "Get a list of top tourist attractions for a given city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The name of the city to find attractions for.",
                        }
                    },
                    "required": ["city"],
                },
            },
        },
    ]


def get_travel_messages():
    """Get travel assistant messages that should trigger multiple tool calls"""
    return [
        {
            "content": "You are a travel assistant providing real-time weather updates and top tourist attractions.",
            "role": "system",
        },
        {
            "content": "I'm planning a trip to Tokyo next week. What's the weather like? What are the most amazing sights?",
            "role": "user",
        },
    ]


def test_non_streaming(client, model_name, tools, messages, tool_choice, test_name):
    """Test non-streaming mode with given tool_choice"""
    print(f"\n{'=' * 60}")
    print(f"Testing NON-STREAMING: {test_name}")
    print(f"tool_choice: {tool_choice}")
    print(f"{'=' * 60}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=200,
            tools=tools,
            tool_choice=tool_choice,
            stream=False,
        )

        print("✅ Request successful")
        print(f"Content: {response.choices[0].message.content}")
        print(f"Tool calls: {response.choices[0].message.tool_calls}")

        # Validate based on tool_choice
        tool_calls = response.choices[0].message.tool_calls
        if tool_choice == "required":
            assert (
                tool_calls is not None and len(tool_calls) > 0
            ), "Expected tool calls when tool_choice='required'"
            print("✅ PASS: Tool calls present when required")
        elif isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            expected_name = tool_choice["function"]["name"]
            assert (
                tool_calls is not None and len(tool_calls) > 0
            ), f"Expected tool calls when tool_choice specifies {expected_name}"
            actual_name = tool_calls[0].function.name
            assert (
                actual_name == expected_name
            ), f"Expected function {expected_name}, got {actual_name}"
            print(f"✅ PASS: Correct function called: {actual_name}")
        elif tool_choice == "auto":
            print(f"ℹ️  INFO: Auto mode - tool calls: {tool_calls is not None}")

        return True

    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_streaming(client, model_name, tools, messages, tool_choice, test_name):
    """Test streaming mode with given tool_choice"""
    print(f"\n{'=' * 60}")
    print(f"Testing STREAMING: {test_name}")
    print(f"tool_choice: {tool_choice}")
    print(f"{'=' * 60}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=200,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
        )

        print("✅ Request successful")

        # Collect streaming response
        content_chunks = []
        tool_call_chunks = []

        for chunk in response:
            if chunk.choices[0].delta.content:
                content_chunks.append(chunk.choices[0].delta.content)
            elif chunk.choices[0].delta.tool_calls:
                tool_call_chunks.extend(chunk.choices[0].delta.tool_calls)

        full_content = "".join(content_chunks)
        print(f"Content: {full_content}")
        print(f"Tool call chunks: {len(tool_call_chunks)}")

        # Validate based on tool_choice
        if tool_choice == "required":
            assert (
                len(tool_call_chunks) > 0
            ), "Expected tool call chunks when tool_choice='required'"
            print("✅ PASS: Tool call chunks present when required")
        elif isinstance(tool_choice, dict) and tool_choice.get("type") == "function":
            expected_name = tool_choice["function"]["name"]
            assert (
                len(tool_call_chunks) > 0
            ), f"Expected tool call chunks when tool_choice specifies {expected_name}"
            # Find function name in chunks
            found_name = None
            for chunk in tool_call_chunks:
                if chunk.function and chunk.function.name:
                    found_name = chunk.function.name
                    break
            assert (
                found_name == expected_name
            ), f"Expected function {expected_name}, got {found_name}"
            print(f"✅ PASS: Correct function called: {found_name}")
        elif tool_choice == "auto":
            print(f"ℹ️  INFO: Auto mode - tool call chunks: {len(tool_call_chunks)}")

        return True

    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return False


def test_multi_tool_non_streaming(
    client, model_name, tools, messages, tool_choice, test_name
):
    """Test non-streaming mode expecting multiple tool calls"""
    print(f"\n{'=' * 60}")
    print(f"Testing MULTI-TOOL NON-STREAMING: {test_name}")
    print(f"tool_choice: {tool_choice}")
    print(f"{'=' * 60}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=400,
            temperature=0.8,
            top_p=0.8,
            tools=tools,
            tool_choice=tool_choice,
            stream=False,
        )

        print("✅ Request successful")
        print(f"Content: {response.choices[0].message.content}")
        print(f"Tool calls: {response.choices[0].message.tool_calls}")

        # Validate based on tool_choice and expected functions
        tool_calls = response.choices[0].message.tool_calls
        expected_functions = {"get_weather", "get_tourist_attractions"}
        is_flaky = False

        if tool_choice in ["required", "auto"]:
            if tool_choice == "auto" and (tool_calls is None or len(tool_calls) == 0):
                print(
                    "ℹ️  INFO: Auto mode got 0 tool calls - this is flaky but acceptable"
                )
                is_flaky = True
                return {"success": True, "flaky": is_flaky}

            assert (
                tool_calls is not None and len(tool_calls) > 0
            ), f"Expected tool calls when tool_choice='{tool_choice}'"

            called_functions = set()
            for call in tool_calls:
                called_functions.add(call.function.name)
                print(
                    f"  - Called: {call.function.name} with args: {call.function.arguments}"
                )

            # For this specific travel scenario, we expect both functions to be called
            if tool_choice == "required":
                # With required, we should get at least one tool call, ideally both
                print(
                    f"✅ PASS: Tool calls present when required ({len(tool_calls)} calls)"
                )
                if expected_functions.issubset(called_functions):
                    print("✅ BONUS: Both expected functions called!")
                else:
                    print(
                        f"ℹ️  INFO: Called {called_functions}, expected both {expected_functions}"
                    )
            elif tool_choice == "auto":
                print(f"ℹ️  INFO: Auto mode - got {len(tool_calls)} tool calls")
                if expected_functions.issubset(called_functions):
                    print("✅ BONUS: Both expected functions called!")

        return {"success": True, "flaky": is_flaky}

    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return {"success": False, "flaky": False}


def test_multi_tool_streaming(
    client, model_name, tools, messages, tool_choice, test_name
):
    """Test streaming mode expecting multiple tool calls"""
    print(f"\n{'=' * 60}")
    print(f"Testing MULTI-TOOL STREAMING: {test_name}")
    print(f"tool_choice: {tool_choice}")
    print(f"{'=' * 60}")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=400,
            temperature=0.8,
            top_p=0.8,
            tools=tools,
            tool_choice=tool_choice,
            stream=True,
        )

        print("✅ Request successful")

        # Collect streaming response
        content_chunks = []
        tool_call_chunks = []

        for chunk in response:
            if chunk.choices[0].delta.content:
                content_chunks.append(chunk.choices[0].delta.content)
            elif chunk.choices[0].delta.tool_calls:
                tool_call_chunks.extend(chunk.choices[0].delta.tool_calls)

        full_content = "".join(content_chunks)
        print(f"Content: {full_content}")
        print(f"Tool call chunks: {len(tool_call_chunks)}")

        # Collect function names from chunks
        called_functions = set()
        for chunk in tool_call_chunks:
            if chunk.function and chunk.function.name:
                called_functions.add(chunk.function.name)
                print(f"  - Found function: {chunk.function.name}")

        expected_functions = {"get_weather", "get_tourist_attractions"}
        is_flaky = False

        # Validate based on tool_choice
        if tool_choice in ["required", "auto"]:
            if tool_choice == "auto" and len(tool_call_chunks) == 0:
                print(
                    "ℹ️  INFO: Auto mode got 0 tool call chunks - this is flaky but acceptable"
                )
                is_flaky = True
                return {"success": True, "flaky": is_flaky}

            assert (
                len(tool_call_chunks) > 0
            ), f"Expected tool call chunks when tool_choice='{tool_choice}'"

            if tool_choice == "required":
                print(
                    f"✅ PASS: Tool call chunks present when required ({len(tool_call_chunks)} chunks)"
                )
                if expected_functions.issubset(called_functions):
                    print("✅ BONUS: Both expected functions found in chunks!")
                else:
                    print(
                        f"ℹ️  INFO: Found {called_functions}, expected both {expected_functions}"
                    )
            elif tool_choice == "auto":
                print(
                    f"ℹ️  INFO: Auto mode - got {len(tool_call_chunks)} tool call chunks"
                )
                if expected_functions.issubset(called_functions):
                    print("✅ BONUS: Both expected functions found in chunks!")

        return {"success": True, "flaky": is_flaky}

    except Exception as e:
        print(f"❌ FAIL: {str(e)}")
        return {"success": False, "flaky": False}


def main():
    """Main test function"""
    print("🧪 Starting tool_choice functionality tests...")

    # Setup
    client, model_name = setup_client()

    # =================================================================
    # Test Suite 1: Single Tool Choice Tests
    # =================================================================
    print(f"\n{'=' * 80}")
    print("📋 TEST SUITE 1: Single Tool Choice Tests")
    print(f"{'=' * 80}")

    tools = get_test_tools()
    messages = get_test_messages()

    # Test cases for single tool scenarios
    single_tool_test_cases = [
        ("auto", "Tool choice AUTO"),
        ("required", "Tool choice REQUIRED"),
        (
            {"type": "function", "function": {"name": "get_weather"}},
            "Tool choice SPECIFIC: get_weather",
        ),
        (
            {"type": "function", "function": {"name": "get_pokemon_info"}},
            "Tool choice SPECIFIC: get_pokemon_info",
        ),
        (
            {"type": "function", "function": {"name": "make_next_step_decision"}},
            "Tool choice SPECIFIC: make_next_step_decision",
        ),
    ]

    single_tool_results = []

    # Run single tool tests
    for tool_choice, test_name in single_tool_test_cases:
        # Test non-streaming
        non_stream_result = test_non_streaming(
            client, model_name, tools, messages, tool_choice, test_name
        )

        # Test streaming
        stream_result = test_streaming(
            client, model_name, tools, messages, tool_choice, test_name
        )

        single_tool_results.append(
            {
                "test_name": test_name,
                "tool_choice": tool_choice,
                "non_streaming": non_stream_result,
                "streaming": stream_result,
            }
        )

    # =================================================================
    # Test Suite 2: Multi-Tool Travel Assistant Tests
    # =================================================================
    print(f"\n{'=' * 80}")
    print("📋 TEST SUITE 2: Multi-Tool Travel Assistant Tests")
    print(f"{'=' * 80}")

    travel_tools = get_travel_tools()
    travel_messages = get_travel_messages()

    # Test cases for multi-tool scenarios (expecting both get_weather and get_tourist_attractions)
    multi_tool_test_cases = [
        ("auto", "Multi-Tool AUTO (Travel Assistant)"),
        ("required", "Multi-Tool REQUIRED (Travel Assistant)"),
    ]

    multi_tool_results = []

    # Run multi-tool tests
    for tool_choice, test_name in multi_tool_test_cases:
        # Test non-streaming
        non_stream_result = test_multi_tool_non_streaming(
            client, model_name, travel_tools, travel_messages, tool_choice, test_name
        )

        # Test streaming
        stream_result = test_multi_tool_streaming(
            client, model_name, travel_tools, travel_messages, tool_choice, test_name
        )

        multi_tool_results.append(
            {
                "test_name": test_name,
                "tool_choice": tool_choice,
                "non_streaming": non_stream_result["success"],
                "streaming": stream_result["success"],
                "non_streaming_flaky": non_stream_result.get("flaky", False),
                "streaming_flaky": stream_result.get("flaky", False),
            }
        )

    # =================================================================
    # Summary
    # =================================================================
    all_results = single_tool_results + multi_tool_results

    print(f"\n{'=' * 80}")
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'=' * 80}")

    print(f"\n🗳️  Model: {model_name}")

    total_tests = len(all_results) * 2  # non-streaming + streaming
    passed_tests = sum(
        [1 for r in all_results if r["non_streaming"]]
        + [1 for r in all_results if r["streaming"]]
    )

    print("\n🔸 Single Tool Choice Tests:")
    for result in single_tool_results:
        ns_status = "✅ PASS" if result["non_streaming"] else "❌ FAIL"
        s_status = "✅ PASS" if result["streaming"] else "❌ FAIL"
        print(f"  {result['test_name']}")
        print(f"    Non-streaming: {ns_status}")
        print(f"    Streaming: {s_status}")

    print("\n🔸 Multi-Tool Travel Assistant Tests:")
    for result in multi_tool_results:
        ns_status = "✅ PASS" if result["non_streaming"] else "❌ FAIL"
        s_status = "✅ PASS" if result["streaming"] else "❌ FAIL"

        # Add flaky indicators
        if result.get("non_streaming_flaky", False):
            ns_status += " (FLAKY)"
        if result.get("streaming_flaky", False):
            s_status += " (FLAKY)"

        print(f"  {result['test_name']}")
        print(f"    Non-streaming: {ns_status}")
        print(f"    Streaming: {s_status}")

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
