
import sys
import os
import json

# Add current directory to path so we can import services
sys.path.append(os.getcwd())

from services import AIService, ConfigService

def test_intent():
    config_service = ConfigService(config_dir="../config")
    ai_service = AIService()
    
    kpi_config = config_service.get_kpi_config()
    ui_mappings = config_service.get_ui_mappings()
    
    test_queries = [
        "机台数量分析",
        "FE人数分析",
        "机台数量统计",
        "分析一下chamber数量"
    ]
    
    print("Testing Intent Recognition...")
    for query in test_queries:
        print(f"\nQuery: {query}")
        result = ai_service.analyze_intent(query, kpi_config, ui_mappings)
        print(f"Result: {result.get('kpi')}")
        
        expected = None
        if "机台" in query or "machine" in query.lower(): expected = "machine_count"
        elif "fe" in query.lower(): expected = "fe_count"
        elif "chamber" in query.lower(): expected = "chamber_count"
        
        if result.get('kpi') == expected:
            print("✅ PASS")
        else:
            print(f"❌ FAIL (Expected {expected})")

if __name__ == "__main__":
    test_intent()
