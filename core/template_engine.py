from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound
from pathlib import Path
import re


class TemplateEngine:
    """Handle SMS template rendering with variable substitution"""
    
    def __init__(self, templates_dir):
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            variable_start_string='{{',
            variable_end_string='}}',
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def list_templates(self):
        """List all available templates"""
        templates = []
        for template_file in self.templates_dir.glob('*.txt'):
            templates.append({
                'name': template_file.stem,
                'file': template_file.name,
                'path': str(template_file)
            })
        return templates
    
    def get_template_content(self, template_name):
        """Get raw template content"""
        template_path = self.templates_dir / f"{template_name}.txt"
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_variables(self, template_content):
        """Extract all variables from template content"""
        # Match {{variable}} pattern
        pattern = r'\{\{(\s*[\w\d_]+\s*)\}\}'
        matches = re.findall(pattern, template_content)
        return list(set([match.strip() for match in matches]))
    
    def render(self, template_name, variables):
        """
        Render a template with given variables
        
        Args:
            template_name: Name of the template (without .txt extension)
            variables: Dictionary of variable names and values
        
        Returns:
            Rendered message string
        """
        try:
            template = self.env.get_template(f"{template_name}.txt")
            return template.render(**variables)
        except TemplateNotFound:
            raise FileNotFoundError(f"Template '{template_name}' not found")
        except Exception as e:
            raise Exception(f"Error rendering template: {str(e)}")
    
    def render_from_string(self, template_string, variables):
        """Render a template from a string instead of file"""
        template = Template(template_string)
        return template.render(**variables)
    
    def create_template(self, name, content):
        """Create a new template file"""
        template_path = self.templates_dir / f"{name}.txt"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return template_path
    
    def delete_template(self, name):
        """Delete a template file"""
        template_path = self.templates_dir / f"{name}.txt"
        if template_path.exists():
            template_path.unlink()
            return True
        return False
    
    def preview_template(self, template_name, variables):
        """Preview template with variables and show metadata"""
        content = self.get_template_content(template_name)
        rendered = self.render(template_name, variables)
        
        # Calculate SMS segments (160 chars per segment for GSM-7, 70 for Unicode)
        length = len(rendered)
        # Check if message contains non-GSM characters (simplified check)
        has_unicode = any(ord(char) > 127 for char in rendered)
        chars_per_segment = 70 if has_unicode else 160
        segments = (length // chars_per_segment) + (1 if length % chars_per_segment > 0 else 0)
        
        return {
            'raw': content,
            'rendered': rendered,
            'length': length,
            'segments': segments,
            'has_unicode': has_unicode,
            'variables_used': self.extract_variables(content),
            'variables_provided': list(variables.keys())
        }
    
    def validate_template(self, template_name, variables):
        """Validate that all required variables are provided"""
        content = self.get_template_content(template_name)
        required_vars = set(self.extract_variables(content))
        provided_vars = set(variables.keys())
        
        missing = required_vars - provided_vars
        extra = provided_vars - required_vars
        
        return {
            'valid': len(missing) == 0,
            'missing_variables': list(missing),
            'extra_variables': list(extra),
            'required_variables': list(required_vars)
        }
