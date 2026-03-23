import pandas as pd
import yaml
import time
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CreatorOutreachGenerator:
    def __init__(self, config_path="config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.client = OpenAI(api_key=self.config['openai']['api_key'])
        self.styles = self.config['styles']
        self.business = self.config['business']

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=2, max=10))
    def _call_openai(self, messages):
        response = self.client.chat.completions.create(
            model=self.config['openai']['model'],
            messages=messages,
            temperature=self.config['openai']['temperature']
        )
        return response.choices[0].message.content.strip()

    def generate_messages(self, nickname, followers, bio=""):
        results = {}
        
        base_info = f"""
        Brand: {self.business['brand_name']}
        Product: {self.business['product_type']}
        Offer: {self.business['offer']}
        Creator: {nickname} ({followers} followers)
        Bio: {bio}
        """
        
        for style_key, style_config in self.styles.items():
            system_prompt = f"""Write a TikTok collaboration DM. 
            Tone: {style_config['tone']}
            Length: 100-150 characters.
            Include: Hook + free product + commission + CTA.
            Language: English."""
            
            user_prompt = f"Generate {style_config['name']} style message for: {base_info}"
            
            try:
                message = self._call_openai([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ])
                results[f"{style_key}_message"] = message
                time.sleep(0.3)  # Avoid rate limit
            except Exception as e:
                results[f"{style_key}_message"] = f"Error: {str(e)}"
        
        return results

    def process_csv(self, input_path, output_path):
        try:
            df = pd.read_csv(input_path)
            logger.info(f"Loaded {len(df)} rows")
            
            # Add result columns
            for col in ['friendly_message', 'direct_message', 'curious_message', 'ai_recommendation']:
                df[col] = ""
            
            for index, row in df.iterrows():
                nickname = str(row['nickname'])
                followers = int(row['followers']) if pd.notna(row['followers']) else 0
                bio = str(row.get('bio', ''))
                
                logger.info(f"Processing {index+1}/{len(df)}: {nickname}")
                
                messages = self.generate_messages(nickname, followers, bio)
                
                df.at[index, 'friendly_message'] = messages['friendly_message']
                df.at[index, 'direct_message'] = messages['direct_message']
                df.at[index, 'curious_message'] = messages['curious_message']
                df.at[index, 'ai_recommendation'] = 'friendly' if followers < 10000 else 'direct'
            
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            return True, f"Success! Processed {len(df)} creators"
            
        except Exception as e:
            logger.error(f"Failed: {str(e)}")
            return False, f"Failed: {str(e)}"