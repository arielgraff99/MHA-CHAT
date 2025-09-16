import openai
from typing import Dict, Any, Optional
from datetime import datetime
from ..config import config

class BriefRefiner:
    """Refine investigation briefs using LLM"""
    
    def __init__(self):
        if config.OPENAI_API_KEY:
            openai.api_key = config.OPENAI_API_KEY
        self.system_prompt = """You are refining an investigation brief. Transform user input into a crisp, objective scope statement with measurable criteria. Ask targeted questions only if needed. Return a single paragraph plus bullet acceptance criteria.

Guidelines:
- Be objective and factual
- Focus on measurable, observable criteria
- Avoid speculation or assumptions
- Keep the scope clear and bounded
- Include temporal boundaries if specified
- Identify key entities (people, organizations, events)

Format your response as:
REFINED_BRIEF: [Single paragraph describing the investigation scope]

ACCEPTANCE_CRITERIA:
• [Specific criterion 1]
• [Specific criterion 2]
• [Additional criteria as needed]"""
    
    def refine_brief(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Refine user's investigation brief
        
        Args:
            user_input: Raw user input describing what they want to investigate
            context: Optional context from previous refinements
        
        Returns:
            Dict containing refined brief, acceptance criteria, and confidence
        """
        try:
            if not config.OPENAI_API_KEY:
                # Fallback to basic refinement without LLM
                return self._basic_refinement(user_input)
            
            # Prepare prompt
            prompt = f"User wants to investigate: {user_input}"
            if context:
                prompt += f"\n\nPrevious context: {context}"
            
            # Call LLM (compatible with both old and new OpenAI API)
            try:
                # Try new API first (OpenAI v1.0+)
                from openai import OpenAI
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                content = response.choices[0].message.content
            except ImportError:
                # Fallback to legacy API
                response = openai.ChatCompletion.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                                 content = response.choices[0].message.content
            
            # Parse response
            return self._parse_llm_response(content, user_input)
            
        except Exception as e:
            print(f"LLM refinement failed: {str(e)}")
            return self._basic_refinement(user_input)
    
    def _parse_llm_response(self, content: str, original_input: str) -> Dict[str, Any]:
        """Parse LLM response into structured format"""
        lines = content.split('\n')
        refined_brief = ""
        acceptance_criteria = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('REFINED_BRIEF:'):
                current_section = 'brief'
                refined_brief = line.replace('REFINED_BRIEF:', '').strip()
            elif line.startswith('ACCEPTANCE_CRITERIA:'):
                current_section = 'criteria'
            elif line.startswith('•') or line.startswith('-'):
                if current_section == 'criteria':
                    criterion = line.lstrip('•-').strip()
                    if criterion:
                        acceptance_criteria.append(criterion)
            elif current_section == 'brief' and line:
                refined_brief += " " + line
        
        # Fallback if parsing failed
        if not refined_brief:
            refined_brief = content.strip()
        
        return {
            'original_input': original_input,
            'refined_brief': refined_brief.strip(),
            'acceptance_criteria': acceptance_criteria,
            'confidence': 0.8 if acceptance_criteria else 0.6,
            'refinement_method': 'llm',
            'needs_confirmation': True
        }
    
    def _basic_refinement(self, user_input: str) -> Dict[str, Any]:
        """Basic refinement without LLM"""
        # Simple cleanup and structuring
        refined = user_input.strip()
        
        # Basic improvements
        if not refined.endswith('.'):
            refined += '.'
        
        # Extract basic criteria
        criteria = []
        if 'between' in refined.lower() and 'and' in refined.lower():
            criteria.append("Temporal boundaries specified")
        if any(word in refined.lower() for word in ['who', 'what', 'when', 'where', 'why', 'how']):
            criteria.append("Investigation questions identified")
        
        return {
            'original_input': user_input,
            'refined_brief': f"Investigation focus: {refined}",
            'acceptance_criteria': criteria or ["Investigation scope defined"],
            'confidence': 0.4,
            'refinement_method': 'basic',
            'needs_confirmation': True
        }
    
    def confirm_refinement(self, refinement_result: Dict[str, Any], user_confirmed: bool) -> Dict[str, Any]:
        """Process user confirmation of refinement"""
        refinement_result['confirmed'] = user_confirmed
        refinement_result['confirmation_timestamp'] = datetime.utcnow().isoformat()
        
        if not user_confirmed:
            refinement_result['status'] = 'rejected'
        else:
            refinement_result['status'] = 'confirmed'
        
        return refinement_result

# Global brief refiner instance
brief_refiner = BriefRefiner()