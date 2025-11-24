#!/usr/bin/env python3
"""
AI Fix Generator
================

Uses Groq AI to generate code fixes for detected issues.
This is Brain's "thinking" module for self-fixing.
"""

import os
from groq import Groq
from typing import Dict, Optional
from datetime import datetime


class AIFixGenerator:
    """Generates code fixes using Groq AI (Llama 3.3 70B)"""
    
    def __init__(self):
        self.groq_api_key = os.getenv('GROQ_API_KEY')
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        self.client = Groq(api_key=self.groq_api_key)
        self.model = "llama-3.3-70b-versatile"
        
        print(f"🤖 AI Fix Generator initialized (Model: {self.model})")
    
    async def generate_fix(
        self,
        issue_description: str,
        current_code: str,
        file_path: str,
        issue_type: str
    ) -> Optional[Dict]:
        """
        Generate a code fix using AI
        
        Args:
            issue_description: Description of the problem
            current_code: Current code content
            file_path: Path to the file
            issue_type: Type of issue
            
        Returns:
            Dict with fixed_code, explanation, confidence, risk_assessment
        """
        
        prompt = f"""You are TheBrain, an autonomous AI that fixes its own code.

**YOUR MISSION:** Fix the following issue in your codebase.

**FILE:** {file_path}
**ISSUE TYPE:** {issue_type}
**ISSUE:** {issue_description}

**CURRENT CODE:**
```python
{current_code[:3000]}  # First 3000 chars
```

**INSTRUCTIONS:**
1. Analyze the issue carefully
2. Generate the COMPLETE fixed code
3. Explain what you changed and why
4. Assess the risk level (low/medium/high)
5. Rate your confidence (0-100%)

**RESPONSE FORMAT (JSON):**
{{
    "fixed_code": "<complete fixed code here>",
    "explanation": "<detailed explanation of changes>",
    "changes_made": ["<change 1>", "<change 2>", "..."],
    "risk_level": "low|medium|high",
    "confidence": <0-100>,
    "testing_needed": true|false,
    "breaking_changes": true|false
}}

**IMPORTANT:**
- Return ONLY valid JSON
- Include the COMPLETE fixed code
- Be thorough but concise
- Consider edge cases
- Maintain code style and patterns
"""

        try:
            print(f"🧠 Generating fix for: {issue_description[:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Python developer and autonomous AI that fixes code. You always return valid JSON responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent fixes
                max_tokens=4000
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse JSON response  
            import json
            import re
            try:
                # Try to extract JSON if wrapped in markdown
                if "```json" in ai_response:
                    ai_response = ai_response.split("```json")[1].split("```")[0]
                elif "```" in ai_response:
                    ai_response = ai_response.split("```")[1].split("```")[0]
                
                # Clean up the response (AI sometimes adds extra formatting)
                ai_response = ai_response.strip()
                
                # Parse JSON with strict=False to handle control characters
                fix_data = json.loads(ai_response, strict=False)
                
                # Validate response
                required_fields = ['fixed_code', 'explanation', 'confidence']
                if not all(field in fix_data for field in required_fields):
                    print(f"⚠️  Invalid AI response - missing fields")
                    return None
                
                print(f"✅ Fix generated!")
                print(f"   Confidence: {fix_data['confidence']}%")
                print(f"   Risk: {fix_data.get('risk_level', 'unknown')}")
                
                return fix_data
                
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse AI response as JSON: {e}")
                print(f"   Response: {ai_response[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Error generating fix: {e}")
            return None
    
    async def validate_fix(self, fixed_code: str, original_code: str) -> Dict:
        """
        Validate that the fix is safe and doesn't break things
        
        Args:
            fixed_code: The proposed fix
            original_code: Original code
            
        Returns:
            Dict with validation results
        """
        
        prompt = f"""You are a code reviewer. Validate this code fix.

**ORIGINAL CODE:**
```python
{original_code[:2000]}
```

**PROPOSED FIX:**
```python
{fixed_code[:2000]}
```

**VALIDATION CHECKLIST:**
1. Does it fix the issue without breaking functionality?
2. Are there any syntax errors?
3. Are there any security concerns?
4. Are there any performance issues?
5. Does it follow Python best practices?

**RESPONSE FORMAT (JSON):**
{{
    "is_safe": true|false,
    "syntax_valid": true|false,
    "potential_issues": ["<issue 1>", "<issue 2>", "..."],
    "recommendation": "approve|reject|needs_review",
    "reasoning": "<explanation>"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a code reviewer. You always return valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            import json
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0]
            
            validation = json.loads(ai_response.strip())
            
            print(f"🔍 Validation: {validation.get('recommendation', 'unknown')}")
            
            return validation
            
        except Exception as e:
            print(f"⚠️  Validation error: {e}")
            return {
                "is_safe": False,
                "recommendation": "needs_review",
                "reasoning": f"Validation failed: {e}"
            }


if __name__ == "__main__":
    import asyncio
    
    async def test_generator():
        generator = AIFixGenerator()
        
        # Test with a mock issue
        test_code = """
def process_signals(self):
    # Invalid channel username
    channels = ['@invalid_channel_123', '@another_bad_one']
    for channel in channels:
        self.listen(channel)
"""
        
        print("\n🧪 Testing AI Fix Generator\n")
        
        fix = await generator.generate_fix(
            issue_description="UsernameInvalidError: Invalid Telegram channel usernames",
            current_code=test_code,
            file_path="modules/the_ear.py",
            issue_type="invalid_config"
        )
        
        if fix:
            print(f"\n✅ Generated Fix:")
            print(f"   Explanation: {fix['explanation'][:100]}...")
            print(f"   Confidence: {fix['confidence']}%")
            print(f"\n   Fixed Code Preview:")
            print(fix['fixed_code'][:200])
            
            # Validate
            print("\n🔍 Validating fix...")
            validation = await generator.validate_fix(fix['fixed_code'], test_code)
            print(f"   Recommendation: {validation.get('recommendation')}")
    
    asyncio.run(test_generator())
