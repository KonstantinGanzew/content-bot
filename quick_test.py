#!/usr/bin/env python3
"""
Быстрый тест бота
"""

import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

async def quick_test():
    """Быстрая проверка работы бота"""
    print("🔍 БЫСТРАЯ ПРОВЕРКА БОТА")
    print("=" * 25)
    
    try:
        from parsers.joyreactor_parser import JoyReactorParser
        from parsers.base_parser import PostData
        
        print("✅ Импорты работают")
        
        # Тест парсера
        print("🔄 Тестирую парсер...")
        parser = JoyReactorParser()
        
        async with parser:
            posts = await parser.parse_posts(3)
            print(f"📊 Найдено постов: {len(posts)}")
            
            if posts:
                for i, post in enumerate(posts, 1):
                    emoji = "🎥" if post.is_video() else "🖼️"
                    print(f"  {i}. {emoji} {post.title[:40]}...")
                    print(f"      ID: {post.post_id}")
                    print(f"      Тип: {post.media_type}")
                    print(f"      URL: {post.media_url[:60]}...")
                
                print(f"\n💡 СТАТИСТИКА:")
                video_count = sum(1 for p in posts if p.is_video())
                image_count = sum(1 for p in posts if p.is_image())
                print(f"   🎥 Видео: {video_count}")
                print(f"   🖼️ Изображения: {image_count}")
                
                # Проверяем есть ли кириллические URL
                cyrillic_posts = [p for p in posts if any(ord(c) > 127 for c in p.media_url)]
                if cyrillic_posts:
                    print(f"   🔤 Постов с кириллицей в URL: {len(cyrillic_posts)}")
                    print(f"      (автоматически обрабатываются fallback стратегией)")
                
                print(f"\n🎯 РЕЗУЛЬТАТ: Бот работает! Найдено {len(posts)} постов")
                return True
            else:
                print("⚠️ Посты не найдены - возможно все уже отправлены")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    if success:
        print("\n💡 Для запуска бота используйте: venv\\Scripts\\python.exe main.py")
    else:
        print("\n💡 Для диагностики смотрите: diagnostic_steps.md") 