from flask import Blueprint, request, jsonify
import openai
import json
import re
from typing import Dict, List, Any

ai_engine_bp = Blueprint('ai_engine', __name__)

class CodeGenerator:
    def __init__(self):
        self.templates = {
            'react_app': {
                'files': {
                    'package.json': self._get_react_package_json,
                    'src/App.js': self._get_react_app_js,
                    'src/index.js': self._get_react_index_js,
                    'src/App.css': self._get_react_app_css,
                    'public/index.html': self._get_react_index_html
                }
            },
            'simple_website': {
                'files': {
                    'index.html': self._get_simple_html,
                    'style.css': self._get_simple_css,
                    'script.js': self._get_simple_js
                }
            }
        }
    
    def _get_react_package_json(self, app_name: str, description: str) -> str:
        return json.dumps({
            "name": app_name.lower().replace(' ', '-'),
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-scripts": "5.0.1"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            },
            "eslintConfig": {
                "extends": ["react-app", "react-app/jest"]
            },
            "browserslist": {
                "production": [">0.2%", "not dead", "not op_mini all"],
                "development": ["last 1 chrome version", "last 1 firefox version", "last 1 safari version"]
            }
        }, indent=2)
    
    def _get_react_app_js(self, app_name: str, description: str, features: List[str]) -> str:
        components = []
        
        if 'contact_form' in features:
            components.append("""
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    alert('تم إرسال الرسالة بنجاح!');
    setFormData({ name: '', email: '', message: '' });
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };""")
        
        form_jsx = ""
        if 'contact_form' in features:
            form_jsx = """
        <section className="contact-section">
          <h2>تواصل معنا</h2>
          <form onSubmit={handleSubmit} className="contact-form">
            <input
              type="text"
              name="name"
              placeholder="الاسم"
              value={formData.name}
              onChange={handleChange}
              required
            />
            <input
              type="email"
              name="email"
              placeholder="البريد الإلكتروني"
              value={formData.email}
              onChange={handleChange}
              required
            />
            <textarea
              name="message"
              placeholder="الرسالة"
              value={formData.message}
              onChange={handleChange}
              required
            ></textarea>
            <button type="submit">إرسال</button>
          </form>
        </section>"""
        
        return f"""import React, {{ useState }} from 'react';
import './App.css';

function App() {{
  {' '.join(components)}

  return (
    <div className="App">
      <header className="App-header">
        <h1>{app_name}</h1>
        <p>{description}</p>
      </header>
      
      <main>
        <section className="hero-section">
          <h2>مرحباً بك في {app_name}</h2>
          <p>نحن نقدم أفضل الخدمات لعملائنا</p>
        </section>
        {form_jsx}
      </main>
      
      <footer>
        <p>&copy; 2024 {app_name}. جميع الحقوق محفوظة.</p>
      </footer>
    </div>
  );
}}

export default App;"""
    
    def _get_react_index_js(self, app_name: str, description: str) -> str:
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import './App.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
    
    def _get_react_app_css(self, app_name: str, description: str) -> str:
        return """.App {
  text-align: center;
  font-family: 'Arial', sans-serif;
  direction: rtl;
}

.App-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
  color: white;
}

.App-header h1 {
  margin: 0;
  font-size: 2.5rem;
}

.App-header p {
  margin: 10px 0 0 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

main {
  padding: 40px 20px;
}

.hero-section {
  margin-bottom: 40px;
}

.hero-section h2 {
  color: #333;
  font-size: 2rem;
  margin-bottom: 15px;
}

.hero-section p {
  color: #666;
  font-size: 1.1rem;
}

.contact-section {
  max-width: 600px;
  margin: 0 auto;
  background: #f8f9fa;
  padding: 30px;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.contact-section h2 {
  color: #333;
  margin-bottom: 20px;
}

.contact-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.contact-form input,
.contact-form textarea {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 16px;
  font-family: inherit;
}

.contact-form textarea {
  min-height: 120px;
  resize: vertical;
}

.contact-form button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 5px;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.contact-form button:hover {
  transform: translateY(-2px);
}

footer {
  background: #333;
  color: white;
  padding: 20px;
  margin-top: 40px;
}

@media (max-width: 768px) {
  .App-header h1 {
    font-size: 2rem;
  }
  
  .hero-section h2 {
    font-size: 1.5rem;
  }
  
  .contact-section {
    margin: 0 10px;
    padding: 20px;
  }
}"""
    
    def _get_react_index_html(self, app_name: str, description: str) -> str:
        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{description}" />
    <title>{app_name}</title>
  </head>
  <body>
    <noscript>يجب تفعيل JavaScript لتشغيل هذا التطبيق.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    
    def _get_simple_html(self, app_name: str, description: str, features: List[str]) -> str:
        contact_form = ""
        if 'contact_form' in features:
            contact_form = """
    <section class="contact-section">
        <h2>تواصل معنا</h2>
        <form id="contactForm" class="contact-form">
            <input type="text" name="name" placeholder="الاسم" required>
            <input type="email" name="email" placeholder="البريد الإلكتروني" required>
            <textarea name="message" placeholder="الرسالة" required></textarea>
            <button type="submit">إرسال</button>
        </form>
    </section>"""
        
        return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name}</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <header>
        <h1>{app_name}</h1>
        <p>{description}</p>
    </header>
    
    <main>
        <section class="hero-section">
            <h2>مرحباً بك في {app_name}</h2>
            <p>نحن نقدم أفضل الخدمات لعملائنا</p>
        </section>
        {contact_form}
    </main>
    
    <footer>
        <p>&copy; 2024 {app_name}. جميع الحقوق محفوظة.</p>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""
    
    def _get_simple_css(self, app_name: str, description: str) -> str:
        return """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #333;
    direction: rtl;
}

header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    padding: 2rem 1rem;
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

header p {
    font-size: 1.2rem;
    opacity: 0.9;
}

main {
    padding: 2rem 1rem;
    max-width: 1200px;
    margin: 0 auto;
}

.hero-section {
    text-align: center;
    margin-bottom: 3rem;
}

.hero-section h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
    color: #333;
}

.hero-section p {
    font-size: 1.1rem;
    color: #666;
}

.contact-section {
    max-width: 600px;
    margin: 0 auto;
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.contact-section h2 {
    text-align: center;
    margin-bottom: 1.5rem;
    color: #333;
}

.contact-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.contact-form input,
.contact-form textarea {
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-size: 1rem;
    font-family: inherit;
}

.contact-form textarea {
    min-height: 120px;
    resize: vertical;
}

.contact-form button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 5px;
    font-size: 1rem;
    cursor: pointer;
    transition: transform 0.2s;
}

.contact-form button:hover {
    transform: translateY(-2px);
}

footer {
    background: #333;
    color: white;
    text-align: center;
    padding: 1.5rem;
    margin-top: 2rem;
}

@media (max-width: 768px) {
    header h1 {
        font-size: 2rem;
    }
    
    .hero-section h2 {
        font-size: 1.5rem;
    }
    
    .contact-section {
        margin: 0 1rem;
        padding: 1.5rem;
    }
}"""
    
    def _get_simple_js(self, app_name: str, description: str) -> str:
        return """document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.getElementById('contactForm');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get form data
            const formData = new FormData(contactForm);
            const name = formData.get('name');
            const email = formData.get('email');
            const message = formData.get('message');
            
            // Simple validation
            if (!name || !email || !message) {
                alert('يرجى ملء جميع الحقول');
                return;
            }
            
            // Simulate form submission
            alert('تم إرسال الرسالة بنجاح! سنتواصل معك قريباً.');
            
            // Reset form
            contactForm.reset();
        });
    }
    
    // Add smooth scrolling for any anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});"""

    def generate_app(self, user_request: str) -> Dict[str, Any]:
        """Generate application code based on user request"""
        try:
            # Parse user request using OpenAI
            analysis = self._analyze_user_request(user_request)
            
            # Generate code based on analysis
            app_type = analysis.get('app_type', 'simple_website')
            app_name = analysis.get('app_name', 'تطبيقي الجديد')
            description = analysis.get('description', 'تطبيق رائع تم إنشاؤه بواسطة sebaircode')
            features = analysis.get('features', [])
            
            if app_type not in self.templates:
                app_type = 'simple_website'
            
            template = self.templates[app_type]
            generated_files = {}
            
            for file_path, generator_func in template['files'].items():
                if callable(generator_func):
                    generated_files[file_path] = generator_func(app_name, description, features)
                else:
                    generated_files[file_path] = generator_func
            
            return {
                'success': True,
                'app_name': app_name,
                'description': description,
                'app_type': app_type,
                'features': features,
                'files': generated_files,
                'preview_url': f'/preview/{app_name.lower().replace(" ", "-")}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_user_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze user request using OpenAI to extract app requirements"""
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """أنت مساعد ذكي لتحليل طلبات إنشاء التطبيقات. قم بتحليل طلب المستخدم واستخرج المعلومات التالية:
                        1. نوع التطبيق (react_app أو simple_website)
                        2. اسم التطبيق
                        3. وصف التطبيق
                        4. الميزات المطلوبة (مثل contact_form, gallery, blog, etc.)
                        
                        أرجع النتيجة في صيغة JSON فقط."""
                    },
                    {
                        "role": "user",
                        "content": f"طلب المستخدم: {user_request}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback parsing
                return self._fallback_parse(user_request)
                
        except Exception as e:
            print(f"Error in OpenAI analysis: {e}")
            return self._fallback_parse(user_request)
    
    def _fallback_parse(self, user_request: str) -> Dict[str, Any]:
        """Fallback parsing when OpenAI is not available"""
        features = []
        app_type = 'simple_website'
        
        # Simple keyword detection
        if any(word in user_request.lower() for word in ['تواصل', 'اتصال', 'رسالة', 'contact']):
            features.append('contact_form')
        
        if any(word in user_request.lower() for word in ['react', 'ريأكت', 'تفاعلي']):
            app_type = 'react_app'
        
        # Extract app name (simple heuristic)
        app_name = 'تطبيقي الجديد'
        if 'موقع' in user_request:
            app_name = 'موقعي الجديد'
        elif 'تطبيق' in user_request:
            app_name = 'تطبيقي الجديد'
        
        return {
            'app_type': app_type,
            'app_name': app_name,
            'description': 'تطبيق رائع تم إنشاؤه بواسطة sebaircode',
            'features': features
        }

# Initialize the code generator
code_generator = CodeGenerator()

@ai_engine_bp.route('/generate', methods=['POST'])
def generate_app():
    """Generate application based on user request"""
    try:
        data = request.get_json()
        user_request = data.get('request', '')
        
        if not user_request:
            return jsonify({'error': 'طلب المستخدم مطلوب'}), 400
        
        result = code_generator.generate_app(user_request)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_engine_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """Chat with AI to clarify requirements"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        context = data.get('context', [])
        
        if not message:
            return jsonify({'error': 'الرسالة مطلوبة'}), 400
        
        # Build conversation context
        messages = [
            {
                "role": "system",
                "content": """أنت مساعد ذكي لمنصة sebaircode لإنشاء التطبيقات. مهمتك هي:
                1. فهم متطلبات المستخدم لإنشاء التطبيق
                2. طرح أسئلة توضيحية عند الحاجة
                3. تقديم اقتراحات مفيدة
                4. التحدث باللغة العربية بشكل ودود ومهني
                
                عندما تكون المتطلبات واضحة، اقترح على المستخدم البدء في إنشاء التطبيق."""
            }
        ]
        
        # Add context from previous messages
        for msg in context:
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": message})
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'response': ai_response,
            'context': messages + [{"role": "assistant", "content": ai_response}]
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_engine_bp.route('/templates', methods=['GET'])
def get_templates():
    """Get available app templates"""
    templates_info = {
        'react_app': {
            'name': 'تطبيق React',
            'description': 'تطبيق ويب تفاعلي باستخدام React',
            'features': ['واجهة تفاعلية', 'تصميم متجاوب', 'مكونات قابلة لإعادة الاستخدام']
        },
        'simple_website': {
            'name': 'موقع ويب بسيط',
            'description': 'موقع ويب بسيط باستخدام HTML/CSS/JavaScript',
            'features': ['تصميم متجاوب', 'سهولة التخصيص', 'سرعة في التحميل']
        }
    }
    
    return jsonify(templates_info)

