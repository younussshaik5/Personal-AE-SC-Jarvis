"""Tool Executor - Safe execution of workspace commands."""

import subprocess
import shlex
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import Event


class ToolExecutor:
    """Executes allowed tools safely within workspace."""

    # Allowed commands and their restrictions
    ALLOWED_COMMANDS = {
        'ls': {'args': ['-la', '-R'], 'description': 'List files'},
        'grep': {'args': ['-r', '-n'], 'description': 'Search in files'},
        'find': {'args': [], 'description': 'Find files'},
        'cat': {'args': [], 'description': 'Read file'},
        'head': {'args': ['-n', '50'], 'description': 'Show first lines'},
        'tail': {'args': ['-n', '50'], 'description': 'Show last lines'},
        'wc': {'args': [], 'description': 'Count lines/words'},
        'pwd': {'args': [], 'description': 'Print working directory'},
        'du': {'args': ['-sh'], 'description': 'Disk usage'},
        'df': {'args': ['-h'], 'description': 'Disk free space'},
        'file': {'args': [], 'description': 'File type'},
        'stat': {'args': [], 'description': 'File status'},
    }

    def __init__(self, workspace_root: Path):
        self.workspace = workspace_root.resolve()
        self.logger = JARVISLogger("tool_executor")

    def execute(self, command_line: str, event_bus=None) -> Dict[str, Any]:
        """
        Execute a command safely.
        Returns: {'success': bool, 'output': str, 'error': str}
        """
        parts = shlex.split(command_line)
        if not parts:
            return {'success': False, 'output': '', 'error': 'Empty command'}

        cmd = parts[0]

        # Special handling for web_search (always allowed)
        if cmd == 'web_search':
            query = ' '.join(parts[1:]) if len(parts) > 1 else ''
            if not query:
                return {'success': False, 'output': '', 'error': 'web_search requires a query'}
            return self._execute_web_search(query, event_bus)

        if cmd not in self.ALLOWED_COMMANDS:
            return {
                'success': False,
                'output': '',
                'error': f"Command '{cmd}' not allowed. Allowed: {', '.join(self.ALLOWED_COMMANDS.keys())}"
            }

        self.logger.debug("Executing command", command=command_line)

        try:
            # Run command
            result = subprocess.run(
                parts,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"

            response = {
                'success': result.returncode == 0,
                'output': output[:10000],  # limit output
                'error': '' if result.returncode == 0 else f"Exit code {result.returncode}",
                'command': command_line
            }

            # Publish tool.executed event for meta-learning
            if event_bus:
                try:
                    event = Event("tool.executed", "tool_executor", {
                        "tool": cmd,
                        "command": command_line,
                        "success": response['success'],
                        "output_length": len(response['output']),
                        "timestamp": datetime.now().isoformat()
                    })
                    event_bus.publish(event)
                except:
                    pass  # Don't fail execution if event publish fails

            return response

        except subprocess.TimeoutExpired as e:
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out (30s)',
                'command': command_line
            }
        except Exception as e:
            self.logger.error("Command execution failed", error=str(e))
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'command': command_line
            }

    def _execute_web_search(self, query: str, event_bus=None) -> Dict[str, Any]:
        """Perform a web search using configured engine (DuckDuckGo)."""
        try:
            import requests
            from urllib.parse import quote_plus

            engine = getattr(self, 'config_engine', 'duckduckgo')
            max_results = getattr(self, 'config_max_results', 5)

            if engine == 'duckduckgo':
                url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (JARVIS Bot)'
                }
                resp = requests.get(url, headers=headers, timeout=getattr(self, 'config_timeout', 10))
                if resp.status_code != 200:
                    return {'success': False, 'output': '', 'error': f"Search failed: HTTP {resp.status_code}"}

                # Parse HTML for results (simple regex/string search)
                html = resp.text
                results = []
                # DuckDuckGo result blocks: <a class="result__a" href="...">Title</a>
                # and <a class="result__snippet">Snippet</a>
                import re
                # Find result links
                link_pattern = re.compile(r'<a class="result__a" href="([^"]+)".*?>(.*?)</a>', re.DOTALL)
                snippet_pattern = re.compile(r'<a class="result__snippet">(.*?)</a>', re.DOTALL)
                
                links = link_pattern.findall(html)
                snippets = snippet_pattern.findall(html)

                # Pair them
                for i, (href, title_html) in enumerate(links[:max_results]):
                    title = re.sub(r'<[^>]+>', '', title_html).strip()
                    snippet = ''
                    if i < len(snippets):
                        snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                    results.append({
                        'title': title,
                        'url': href,
                        'snippet': snippet
                    })

                # Format output
                output_lines = [f"Web search for: {query}"]
                output_lines.append(f"Engine: DuckDuckGo (HTML)")
                output_lines.append("")
                for i, r in enumerate(results, 1):
                    output_lines.append(f"{i}. {r['title']}")
                    output_lines.append(f"   URL: {r['url']}")
                    if r['snippet']:
                        output_lines.append(f"   {r['snippet']}")
                    output_lines.append("")

                output = "\n".join(output_lines)
            else:
                return {'success': False, 'output': '', 'error': f"Unsupported search engine: {engine}"}

            response = {
                'success': True,
                'output': output[:20000],  # larger limit for web results
                'error': '',
                'command': f"web_search {query}"
            }

            # Publish tool.executed event
            if event_bus:
                try:
                    event = Event("tool.executed", "tool_executor", {
                        "tool": "web_search",
                        "command": f"web_search {query}",
                        "success": True,
                        "results_count": len(results),
                        "timestamp": datetime.now().isoformat()
                    })
                    event_bus.publish(event)
                except:
                    pass

            return response

        except Exception as e:
            self.logger.error("Web search failed", error=str(e))
            return {
                'success': False,
                'output': '',
                'error': f"Web search error: {str(e)}",
                'command': f"web_search {query}"
            }

            # Build safe command (add default args but keep user-specified ones)
            allowed_info = self.ALLOWED_COMMANDS[cmd]
            # For simplicity, just run the command as-is but verify it starts with allowed cmd
            # More sophisticated arg validation would go here

            # Ensure command runs within workspace
            # For commands that accept paths, we could verify they're within workspace
            # But for now, we trust the LLM to use relative paths

            self.logger.debug("Executing command", command=command_line)

            # Run command
            result = subprocess.run(
                parts,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"

            return {
                'success': result.returncode == 0,
                'output': output[:10000],  # limit output
                'error': '' if result.returncode == 0 else f"Exit code {result.returncode}",
                'command': command_line
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'Command timed out (30s)',
                'command': command_line
            }
        except Exception as e:
            self.logger.error("Command execution failed", error=str(e))
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'command': command_line
            }

    def get_allowed_commands(self) -> List[str]:
        """List of allowed command names."""
        return list(self.ALLOWED_COMMANDS.keys())

    def get_tool_descriptions(self) -> List[Dict]:
        """Get tool descriptions for LLM system prompt."""
        return [
            {
                "name": cmd,
                "description": info['description'],
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": f"The full {cmd} command with arguments"
                        }
                    },
                    "required": ["command"]
                }
            }
            for cmd, info in self.ALLOWED_COMMANDS.items()
        ]
