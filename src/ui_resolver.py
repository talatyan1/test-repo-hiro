import json
from openai import OpenAI
from src.config import Config
from src.logger import ai_logger, error_logger

class UIResolver:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Config.PROMPTS_DIR / "ui_healing_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except:
            return "以下の中から {goal} に最も適した要素を特定してJSONで返してください: {elements}"

    async def get_interactive_elements(self, page):
        """ページ内の代表的なインタラクティブ要素を抽出します。"""
        # Playwrightのevaluateを使用してブラウザ側で抽出
        elements = await page.evaluate("""() => {
            const result = [];
            const interactive = document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"]');
            
            interactive.forEach((el, index) => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    result.push({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || "").trim().substring(0, 50),
                        id: el.id,
                        classes: el.className.substring(0, 50),
                        role: el.getAttribute('role') || '',
                        ariaLabel: el.getAttribute('aria-label') || ''
                    });
                }
            });
            return result.slice(0, 50); // トークン節約のため最大50個
        }""")
        return elements

    async def resolve_element(self, page, goal: str):
        """AIを使用して、目標に最も近い要素を特定し、クリックします（またはセレクタを返します）。"""
        elements = await self.get_interactive_elements(page)
        if not elements:
            error_logger.warning("自己修復試行: ページ内にインタラクティブな要素が見つかりませんでした。")
            return False

        prompt = self.prompt_template.format(
            goal=goal,
            elements=json.dumps(elements, ensure_ascii=False, indent=2)
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "出力は必ず指定されたJSONフォーマットのみにしてください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            
            result_json = json.loads(response.choices[0].message.content)
            index = int(result_json.get("index", -1))
            
            if index != -1 and index < len(elements):
                ai_logger.info(f"AIによる自動修復試行: 目標「{goal}」に対して要素 {index} を特定。理由: {result_json.get('reason', '')}")
                
                # 特定した要素をインデックスでクリック
                await page.evaluate(f"""(idx) => {{
                    const interactive = document.querySelectorAll('button, a, input[type="button"], input[type="submit"], [role="button"]');
                    const elements = Array.from(interactive).filter(el => {{
                        const rect = el.getBoundingClientRect();
                        return rect.width > 0 && rect.height > 0;
                    }});
                    if (elements[idx]) elements[idx].click();
                }}""", index)
                
                return True
            else:
                ai_logger.warning(f"AIによる自動修復試行: 目標「{goal}」に該当する要素は見つかりませんでした。")
                return False
                
        except Exception as e:
            error_logger.error(f"AIによるUI要素解析エラー: {e}")
            return False
