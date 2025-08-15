#!/usr/bin/env python3
"""
Documentation Generator for TradingBot Pro
Automatically generates comprehensive documentation from codebase and configuration
"""

import os
import re
import json
import inspect
import importlib
import markdown
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pkgutil
import sys
import ast
from jinja2 import Environment, FileSystemLoader

class DocumentationGenerator:
    def __init__(self, project_root: str, output_dir: str = "docs"):
        self.project_root = os.path.abspath(project_root)
        self.output_dir = os.path.join(self.project_root, output_dir)
        self.logger = logging.getLogger(__name__)
        self.template_dir = os.path.join(self.project_root, "templates", "docs")
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_dir))
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize documentation structure
        self.documentation = {
            "project_name": "TradingBot Pro",
            "version": "1.0.0",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "modules": {},
            "api_endpoints": [],
            "strategies": [],
            "configuration": {},
            "database_schema": [],
            "user_guides": []
        }
    
    def generate_documentation(self):
        """Generate complete documentation"""
        try:
            self.logger.info("Starting documentation generation")
            
            # Parse Python modules
            self._parse_python_modules()
            
            # Extract API endpoints
            self._extract_api_endpoints()
            
            # Document trading strategies
            self._document_trading_strategies()
            
            # Document configuration options
            self._document_configuration()
            
            # Document database schema
            self._document_database_schema()
            
            # Generate user guides
            self._generate_user_guides()
            
            # Generate HTML documentation
            self._generate_html_docs()
            
            # Generate PDF documentation
            self._generate_pdf_docs()
            
            # Generate markdown documentation
            self._generate_markdown_docs()
            
            self.logger.info(f"Documentation generated successfully in {self.output_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Documentation generation failed: {e}")
            return False
    
    def _parse_python_modules(self):
        """Parse Python modules and extract documentation"""
        self.logger.info("Parsing Python modules")
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip documentation directory and hidden directories
            if os.path.basename(root).startswith('.') or self.output_dir in root:
                continue
                
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_root)
                    
                    try:
                        module_doc = self._parse_python_file(file_path, rel_path)
                        if module_doc:
                            module_name = os.path.splitext(rel_path)[0].replace(os.path.sep, '.')
                            self.documentation["modules"][module_name] = module_doc
                    except Exception as e:
                        self.logger.warning(f"Failed to parse {rel_path}: {e}")
    
    def _parse_python_file(self, file_path: str, rel_path: str) -> Dict:
        """Parse a Python file and extract documentation"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        module_doc = {
            "path": rel_path,
            "docstring": "",
            "classes": {},
            "functions": {},
            "imports": [],
            "constants": {}
        }
        
        try:
            tree = ast.parse(content)
            
            # Extract module docstring
            if ast.get_docstring(tree):
                module_doc["docstring"] = ast.get_docstring(tree)
            
            # Extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        module_doc["imports"].append(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        module_doc["imports"].append(f"{module}.{name.name}")
            
            # Extract classes and functions
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_doc = self._parse_class_def(node)
                    module_doc["classes"][node.name] = class_doc
                elif isinstance(node, ast.FunctionDef):
                    func_doc = self._parse_function_def(node)
                    module_doc["functions"][node.name] = func_doc
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            # Assume uppercase variables are constants
                            module_doc["constants"][target.id] = self._get_constant_value(node.value)
            
            return module_doc
            
        except SyntaxError as e:
            self.logger.warning(f"Syntax error in {rel_path}: {e}")
            return module_doc
    
    def _parse_class_def(self, node: ast.ClassDef) -> Dict:
        """Parse a class definition"""
        class_doc = {
            "docstring": ast.get_docstring(node) or "",
            "methods": {},
            "attributes": [],
            "bases": [self._get_name(base) for base in node.bases]
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_doc = self._parse_function_def(item)
                class_doc["methods"][item.name] = method_doc
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        class_doc["attributes"].append(target.id)
        
        return class_doc
    
    def _parse_function_def(self, node: ast.FunctionDef) -> Dict:
        """Parse a function definition"""
        func_doc = {
            "docstring": ast.get_docstring(node) or "",
            "parameters": [],
            "returns": None,
            "decorators": [self._get_name(d) for d in node.decorator_list]
        }
        
        # Extract parameters
        for arg in node.args.args:
            param = {"name": arg.arg, "type_hint": None}
            if arg.annotation:
                param["type_hint"] = self._get_name(arg.annotation)
            func_doc["parameters"].append(param)
        
        # Extract return type from docstring or type hint
        if node.returns:
            func_doc["returns"] = self._get_name(node.returns)
        
        # Parse docstring for return type if not in type hint
        if func_doc["docstring"] and not func_doc["returns"]:
            return_match = re.search(r'Returns:\s*([^\n]+)', func_doc["docstring"])
            if return_match:
                func_doc["returns"] = return_match.group(1).strip()
        
        return func_doc
    
    def _get_name(self, node) -> str:
        """Get the name of a node as a string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_name(node.value)}[{self._get_name(node.slice)}]"
        elif isinstance(node, ast.Call):
            return self._get_name(node.func)
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Index):
            return self._get_name(node.value)
        else:
            return str(node)
    
    def _get_constant_value(self, node) -> str:
        """Get the value of a constant as a string"""
        if isinstance(node, ast.Constant):
            return repr(node.value)
        elif isinstance(node, ast.Dict):
            return "{ ... }"
        elif isinstance(node, ast.List):
            return "[ ... ]"
        elif isinstance(node, ast.Tuple):
            return "( ... )"
        else:
            return "..."
    
    def _extract_api_endpoints(self):
        """Extract API endpoints from Flask routes"""
        self.logger.info("Extracting API endpoints")
        
        # Look for Flask route decorators in the codebase
        api_endpoints = []
        
        for module_name, module_doc in self.documentation["modules"].items():
            for func_name, func_doc in module_doc["functions"].items():
                for decorator in func_doc["decorators"]:
                    if "route" in decorator or "app.route" in decorator:
                        # Extract route path
                        route_match = re.search(r"route\(['\"]([^'\"]+)['\"].*\)", decorator)
                        if route_match:
                            route_path = route_match.group(1)
                            
                            # Extract HTTP methods
                            methods = ["GET"]
                            methods_match = re.search(r"methods=\[([^\]]+)\]", decorator)
                            if methods_match:
                                methods = [m.strip("'\" ") for m in methods_match.group(1).split(',')]
                            
                            endpoint = {
                                "path": route_path,
                                "methods": methods,
                                "function": func_name,
                                "module": module_name,
                                "description": func_doc["docstring"],
                                "parameters": func_doc["parameters"],
                                "returns": func_doc["returns"]
                            }
                            
                            api_endpoints.append(endpoint)
        
        self.documentation["api_endpoints"] = api_endpoints
    
    def _document_trading_strategies(self):
        """Document available trading strategies"""
        self.logger.info("Documenting trading strategies")
        
        strategies = []
        
        # Look for strategy classes in the codebase
        for module_name, module_doc in self.documentation["modules"].items():
            for class_name, class_doc in module_doc["classes"].items():
                # Check if this is a strategy class
                if "Strategy" in class_name or any("Strategy" in base for base in class_doc["bases"]):
                    strategy = {
                        "name": class_name,
                        "module": module_name,
                        "description": class_doc["docstring"],
                        "parameters": [],
                        "methods": []
                    }
                    
                    # Extract strategy parameters from __init__ method
                    if "__init__" in class_doc["methods"]:
                        init_method = class_doc["methods"]["__init__"]
                        strategy["parameters"] = init_method["parameters"]
                    
                    # Extract key methods
                    for method_name, method_doc in class_doc["methods"].items():
                        if method_name not in ["__init__", "__str__", "__repr__"]:
                            strategy["methods"].append({
                                "name": method_name,
                                "description": method_doc["docstring"],
                                "parameters": method_doc["parameters"]
                            })
                    
                    strategies.append(strategy)
        
        self.documentation["strategies"] = strategies
    
    def _document_configuration(self):
        """Document configuration options"""
        self.logger.info("Documenting configuration options")
        
        config = {}
        
        # Look for configuration files
        config_files = [
            os.path.join(self.project_root, "config.py"),
            os.path.join(self.project_root, "config.json"),
            os.path.join(self.project_root, "config.yaml"),
            os.path.join(self.project_root, "config.yml")
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                ext = os.path.splitext(config_file)[1]
                
                if ext == ".py":
                    config.update(self._parse_python_config(config_file))
                elif ext == ".json":
                    config.update(self._parse_json_config(config_file))
                elif ext in [".yaml", ".yml"]:
                    config.update(self._parse_yaml_config(config_file))
        
        # Also look for constants in modules that might be configuration
        for module_name, module_doc in self.documentation["modules"].items():
            if "config" in module_name.lower():
                for const_name, const_value in module_doc["constants"].items():
                    config[const_name] = {
                        "value": const_value,
                        "description": "Configuration constant"
                    }
        
        self.documentation["configuration"] = config
    
    def _parse_python_config(self, config_file: str) -> Dict:
        """Parse Python configuration file"""
        config = {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            name = target.id
                            value = self._get_constant_value(node.value)
                            
                            # Look for comments above the assignment
                            description = ""
                            if hasattr(node, 'lineno') and node.lineno > 1:
                                lines = content.split('\n')
                                line_idx = node.lineno - 2  # Previous line
                                if line_idx >= 0 and '#' in lines[line_idx]:
                                    description = lines[line_idx].split('#')[1].strip()
                            
                            config[name] = {
                                "value": value,
                                "description": description
                            }
        except Exception as e:
            self.logger.warning(f"Failed to parse Python config {config_file}: {e}")
        
        return config
    
    def _parse_json_config(self, config_file: str) -> Dict:
        """Parse JSON configuration file"""
        config = {}
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, value in data.items():
                config[key] = {
                    "value": str(value),
                    "description": "Configuration value"
                }
        except Exception as e:
            self.logger.warning(f"Failed to parse JSON config {config_file}: {e}")
        
        return config
    
    def _parse_yaml_config(self, config_file: str) -> Dict:
        """Parse YAML configuration file"""
        config = {}
        
        try:
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            for key, value in data.items():
                config[key] = {
                    "value": str(value),
                    "description": "Configuration value"
                }
        except ImportError:
            self.logger.warning("PyYAML not installed, skipping YAML config parsing")
        except Exception as e:
            self.logger.warning(f"Failed to parse YAML config {config_file}: {e}")
        
        return config
    
    def _document_database_schema(self):
        """Document database schema"""
        self.logger.info("Documenting database schema")
        
        schema = []
        
        # Look for SQLAlchemy models
        for module_name, module_doc in self.documentation["modules"].items():
            for class_name, class_doc in module_doc["classes"].items():
                # Check if this is a database model
                if "Base" in class_doc["bases"] or "Model" in class_doc["bases"] or "db.Model" in class_doc["bases"]:
                    table = {
                        "name": class_name,
                        "module": module_name,
                        "description": class_doc["docstring"],
                        "columns": []
                    }
                    
                    # Extract columns from attributes
                    for attr in class_doc["attributes"]:
                        # This is a simplified approach - in a real implementation,
                        # we would need to parse the attribute assignments to extract column details
                        table["columns"].append({
                            "name": attr,
                            "type": "Unknown",
                            "description": ""
                        })
                    
                    schema.append(table)
        
        self.documentation["database_schema"] = schema
    
    def _generate_user_guides(self):
        """Generate user guides"""
        self.logger.info("Generating user guides")
        
        # Define standard user guides
        guides = [
            {
                "title": "Getting Started",
                "filename": "getting_started.md",
                "sections": [
                    {"title": "Installation", "content": "Instructions for installing TradingBot Pro."},
                    {"title": "Configuration", "content": "How to configure the system for first use."},
                    {"title": "Quick Start", "content": "Creating your first trading strategy."}
                ]
            },
            {
                "title": "User Interface Guide",
                "filename": "ui_guide.md",
                "sections": [
                    {"title": "Dashboard", "content": "Overview of the dashboard and its components."},
                    {"title": "Strategy Management", "content": "How to create, edit, and manage trading strategies."},
                    {"title": "API Key Management", "content": "Managing exchange API keys."},
                    {"title": "Performance Monitoring", "content": "Tracking and analyzing trading performance."}
                ]
            },
            {
                "title": "Trading Strategies",
                "filename": "trading_strategies.md",
                "sections": [
                    {"title": "Strategy Types", "content": "Overview of available strategy types."},
                    {"title": "Strategy Parameters", "content": "Explanation of strategy parameters and their effects."},
                    {"title": "Creating Custom Strategies", "content": "Guide to creating your own custom strategies."}
                ]
            },
            {
                "title": "Risk Management",
                "filename": "risk_management.md",
                "sections": [
                    {"title": "Position Sizing", "content": "How to configure position sizing for trades."},
                    {"title": "Stop Loss and Take Profit", "content": "Setting up stop loss and take profit levels."},
                    {"title": "Risk Metrics", "content": "Understanding risk metrics and reports."}
                ]
            },
            {
                "title": "Troubleshooting",
                "filename": "troubleshooting.md",
                "sections": [
                    {"title": "Common Issues", "content": "Solutions to common problems."},
                    {"title": "Error Messages", "content": "Explanation of error messages and how to resolve them."},
                    {"title": "Support", "content": "How to get additional support."}
                ]
            }
        ]
        
        # Generate guide content from templates or defaults
        for guide in guides:
            guide_path = os.path.join(self.output_dir, guide["filename"])
            
            # Check if a template exists
            template_path = os.path.join(self.template_dir, guide["filename"])
            if os.path.exists(template_path):
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # Generate default content
                content = f"# {guide['title']}\n\n"
                for section in guide["sections"]:
                    content += f"## {section['title']}\n\n{section['content']}\n\n"
            
            # Write guide file
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        self.documentation["user_guides"] = guides
    
    def _generate_html_docs(self):
        """Generate HTML documentation"""
        self.logger.info("Generating HTML documentation")
        
        # Create HTML output directory
        html_dir = os.path.join(self.output_dir, "html")
        os.makedirs(html_dir, exist_ok=True)
        
        # Load templates
        try:
            index_template = self.jinja_env.get_template("index.html")
            module_template = self.jinja_env.get_template("module.html")
            api_template = self.jinja_env.get_template("api.html")
            strategy_template = self.jinja_env.get_template("strategy.html")
            config_template = self.jinja_env.get_template("config.html")
            schema_template = self.jinja_env.get_template("schema.html")
            guide_template = self.jinja_env.get_template("guide.html")
        except Exception as e:
            self.logger.warning(f"Failed to load templates: {e}. Using default templates.")
            # Create simple default templates
            index_template = self.jinja_env.from_string("""<!DOCTYPE html>
<html>
<head>
    <title>{{ doc.project_name }} Documentation</title>
</head>
<body>
    <h1>{{ doc.project_name }} Documentation</h1>
    <p>Version: {{ doc.version }}</p>
    <p>Generated: {{ doc.generated_at }}</p>
    
    <h2>Contents</h2>
    <ul>
        <li><a href="modules.html">Modules</a></li>
        <li><a href="api.html">API Endpoints</a></li>
        <li><a href="strategies.html">Trading Strategies</a></li>
        <li><a href="config.html">Configuration</a></li>
        <li><a href="schema.html">Database Schema</a></li>
    </ul>
    
    <h2>User Guides</h2>
    <ul>
    {% for guide in doc.user_guides %}
        <li><a href="guides/{{ guide.filename }}.html">{{ guide.title }}</a></li>
    {% endfor %}
    </ul>
</body>
</html>""")
        
        # Generate index page
        index_html = index_template.render(doc=self.documentation)
        with open(os.path.join(html_dir, "index.html"), 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        # Generate module pages
        modules_dir = os.path.join(html_dir, "modules")
        os.makedirs(modules_dir, exist_ok=True)
        
        for module_name, module_doc in self.documentation["modules"].items():
            module_html = module_template.render(name=module_name, module=module_doc, doc=self.documentation)
            safe_name = module_name.replace('.', '_')
            with open(os.path.join(modules_dir, f"{safe_name}.html"), 'w', encoding='utf-8') as f:
                f.write(module_html)
        
        # Generate API documentation
        api_html = api_template.render(doc=self.documentation)
        with open(os.path.join(html_dir, "api.html"), 'w', encoding='utf-8') as f:
            f.write(api_html)
        
        # Generate strategy documentation
        strategy_html = strategy_template.render(doc=self.documentation)
        with open(os.path.join(html_dir, "strategies.html"), 'w', encoding='utf-8') as f:
            f.write(strategy_html)
        
        # Generate configuration documentation
        config_html = config_template.render(doc=self.documentation)
        with open(os.path.join(html_dir, "config.html"), 'w', encoding='utf-8') as f:
            f.write(config_html)
        
        # Generate schema documentation
        schema_html = schema_template.render(doc=self.documentation)
        with open(os.path.join(html_dir, "schema.html"), 'w', encoding='utf-8') as f:
            f.write(schema_html)
        
        # Generate user guide pages
        guides_dir = os.path.join(html_dir, "guides")
        os.makedirs(guides_dir, exist_ok=True)
        
        for guide in self.documentation["user_guides"]:
            # Convert markdown to HTML
            md_path = os.path.join(self.output_dir, guide["filename"])
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            html_content = markdown.markdown(md_content)
            guide_html = guide_template.render(title=guide["title"], content=html_content, doc=self.documentation)
            
            html_filename = os.path.splitext(guide["filename"])[0] + ".html"
            with open(os.path.join(guides_dir, html_filename), 'w', encoding='utf-8') as f:
                f.write(guide_html)
    
    def _generate_pdf_docs(self):
        """Generate PDF documentation"""
        self.logger.info("Generating PDF documentation")
        
        # Create PDF output directory
        pdf_dir = os.path.join(self.output_dir, "pdf")
        os.makedirs(pdf_dir, exist_ok=True)
        
        try:
            import weasyprint
            
            # Convert HTML docs to PDF
            html_dir = os.path.join(self.output_dir, "html")
            
            # Generate main PDF
            index_html_path = os.path.join(html_dir, "index.html")
            if os.path.exists(index_html_path):
                with open(index_html_path, 'r', encoding='utf-8') as f:
                    html = f.read()
                
                pdf = weasyprint.HTML(string=html, base_url=html_dir).write_pdf()
                
                with open(os.path.join(pdf_dir, "documentation.pdf"), 'wb') as f:
                    f.write(pdf)
            
            # Generate user guide PDFs
            guides_dir = os.path.join(html_dir, "guides")
            if os.path.exists(guides_dir):
                for guide in self.documentation["user_guides"]:
                    html_filename = os.path.splitext(guide["filename"])[0] + ".html"
                    html_path = os.path.join(guides_dir, html_filename)
                    
                    if os.path.exists(html_path):
                        with open(html_path, 'r', encoding='utf-8') as f:
                            html = f.read()
                        
                        pdf = weasyprint.HTML(string=html, base_url=guides_dir).write_pdf()
                        
                        pdf_filename = os.path.splitext(guide["filename"])[0] + ".pdf"
                        with open(os.path.join(pdf_dir, pdf_filename), 'wb') as f:
                            f.write(pdf)
            
        except ImportError:
            self.logger.warning("WeasyPrint not installed, skipping PDF generation")
    
    def _generate_markdown_docs(self):
        """Generate Markdown documentation"""
        self.logger.info("Generating Markdown documentation")
        
        # Create markdown output directory
        md_dir = os.path.join(self.output_dir, "markdown")
        os.makedirs(md_dir, exist_ok=True)
        
        # Generate README.md
        readme_content = f"# {self.documentation['project_name']} Documentation\n\n"
        readme_content += f"Version: {self.documentation['version']}\n\n"
        readme_content += f"Generated: {self.documentation['generated_at']}\n\n"
        
        readme_content += "## Contents\n\n"
        readme_content += "* [Modules](modules.md)\n"
        readme_content += "* [API Endpoints](api.md)\n"
        readme_content += "* [Trading Strategies](strategies.md)\n"
        readme_content += "* [Configuration](config.md)\n"
        readme_content += "* [Database Schema](schema.md)\n\n"
        
        readme_content += "## User Guides\n\n"
        for guide in self.documentation["user_guides"]:
            readme_content += f"* [{guide['title']}](guides/{guide['filename']})\n"
        
        with open(os.path.join(md_dir, "README.md"), 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        # Generate modules.md
        modules_content = "# Modules\n\n"
        for module_name, module_doc in self.documentation["modules"].items():
            modules_content += f"## {module_name}\n\n"
            if module_doc["docstring"]:
                modules_content += f"{module_doc['docstring']}\n\n"
            
            if module_doc["classes"]:
                modules_content += "### Classes\n\n"
                for class_name, class_doc in module_doc["classes"].items():
                    modules_content += f"#### {class_name}\n\n"
                    if class_doc["docstring"]:
                        modules_content += f"{class_doc['docstring']}\n\n"
            
            if module_doc["functions"]:
                modules_content += "### Functions\n\n"
                for func_name, func_doc in module_doc["functions"].items():
                    modules_content += f"#### {func_name}\n\n"
                    if func_doc["docstring"]:
                        modules_content += f"{func_doc['docstring']}\n\n"
        
        with open(os.path.join(md_dir, "modules.md"), 'w', encoding='utf-8') as f:
            f.write(modules_content)
        
        # Generate api.md
        api_content = "# API Endpoints\n\n"
        for endpoint in self.documentation["api_endpoints"]:
            api_content += f"## {endpoint['path']}\n\n"
            api_content += f"Methods: {', '.join(endpoint['methods'])}\n\n"
            if endpoint["description"]:
                api_content += f"{endpoint['description']}\n\n"
            
            api_content += f"Function: `{endpoint['function']}` in module `{endpoint['module']}`\n\n"
            
            if endpoint["parameters"]:
                api_content += "### Parameters\n\n"
                for param in endpoint["parameters"]:
                    api_content += f"* `{param['name']}`"
                    if param["type_hint"]:
                        api_content += f" ({param['type_hint']})"
                    api_content += "\n"
                api_content += "\n"
        
        with open(os.path.join(md_dir, "api.md"), 'w', encoding='utf-8') as f:
            f.write(api_content)
        
        # Generate strategies.md
        strategies_content = "# Trading Strategies\n\n"
        for strategy in self.documentation["strategies"]:
            strategies_content += f"## {strategy['name']}\n\n"
            if strategy["description"]:
                strategies_content += f"{strategy['description']}\n\n"
            
            strategies_content += f"Module: `{strategy['module']}`\n\n"
            
            if strategy["parameters"]:
                strategies_content += "### Parameters\n\n"
                for param in strategy["parameters"]:
                    strategies_content += f"* `{param['name']}`"
                    if param["type_hint"]:
                        strategies_content += f" ({param['type_hint']})"
                    strategies_content += "\n"
                strategies_content += "\n"
            
            if strategy["methods"]:
                strategies_content += "### Methods\n\n"
                for method in strategy["methods"]:
                    strategies_content += f"#### {method['name']}\n\n"
                    if method["description"]:
                        strategies_content += f"{method['description']}\n\n"
        
        with open(os.path.join(md_dir, "strategies.md"), 'w', encoding='utf-8') as f:
            f.write(strategies_content)
        
        # Generate config.md
        config_content = "# Configuration\n\n"
        for key, config in self.documentation["configuration"].items():
            config_content += f"## {key}\n\n"
            config_content += f"Value: `{config['value']}`\n\n"
            if config["description"]:
                config_content += f"{config['description']}\n\n"
        
        with open(os.path.join(md_dir, "config.md"), 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # Generate schema.md
        schema_content = "# Database Schema\n\n"
        for table in self.documentation["database_schema"]:
            schema_content += f"## {table['name']}\n\n"
            if table["description"]:
                schema_content += f"{table['description']}\n\n"
            
            schema_content += f"Module: `{table['module']}`\n\n"
            
            if table["columns"]:
                schema_content += "### Columns\n\n"
                schema_content += "| Name | Type | Description |\n"
                schema_content += "|------|------|-------------|\n"
                for column in table["columns"]:
                    schema_content += f"| {column['name']} | {column['type']} | {column['description']} |\n"
                schema_content += "\n"
        
        with open(os.path.join(md_dir, "schema.md"), 'w', encoding='utf-8') as f:
            f.write(schema_content)
        
        # Copy user guides
        guides_dir = os.path.join(md_dir, "guides")
        os.makedirs(guides_dir, exist_ok=True)
        
        for guide in self.documentation["user_guides"]:
            src_path = os.path.join(self.output_dir, guide["filename"])
            dst_path = os.path.join(guides_dir, guide["filename"])
            
            if os.path.exists(src_path):
                with open(src_path, 'r', encoding='utf-8') as src_file:
                    content = src_file.read()
                
                with open(dst_path, 'w', encoding='utf-8') as dst_file:
                    dst_file.write(content)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize documentation generator
    doc_generator = DocumentationGenerator(project_root)
    
    # Generate documentation
    success = doc_generator.generate_documentation()
    
    if success:
        print(f"Documentation generated successfully in {doc_generator.output_dir}")
    else:
        print("Documentation generation failed")