from sqlalchemy import text
from sqlmodel import select, func, SQLModel
import unicodedata

from app.core.config import settings
from app.models.models import User, Archive, Meme, Course, CourseCategory, ArchiveType
from app.utils.auth import get_password_hash
from app.db.session import engine, AsyncSessionLocal

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.commit()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.name == settings.DEFAULT_ADMIN_NAME))
        admin_user = result.scalar_one_or_none()
        
        if not admin_user:
            admin_user = User(
                name=settings.DEFAULT_ADMIN_NAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                password_hash=get_password_hash(settings.DEFAULT_ADMIN_PASSWORD),
                is_local=True,
                is_admin=True
            )
            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

        result = await session.execute(select(func.count()).select_from(Course))
        count = result.scalar()
        if count == 0:
            initial_courses_data = [
                {
                    "name": "微積分(一)",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "微積分(二)",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "物理(一)",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "物理(二)",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "化學(一)",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "化學(二)",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "線性代數",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "計算機概論與程式設計",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "資料結構與物件導向程式設計",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "離散數學",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "數位電路設計",
                    "category": CourseCategory.FRESHMAN
                },
                {
                    "name": "MATLAB 程式語言",
                    "category": CourseCategory.FRESHMAN,
                },
                {
                    "name": "機率",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "演算法概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "計算機組織",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "資料庫系統概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "人工智慧概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "計算機網路概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "密碼學概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "數值方法",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "通訊原理與無線網路",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "數位電路實驗",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "正規語言概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "組合數學",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "訊號與系統",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "數位訊號處理概論",
                    "category": CourseCategory.SOPHOMORE
                },
                {
                    "name": "數位系統設計",
                    "category": CourseCategory.SOPHOMORE,
                },
                {
                    "name": "圖形理論導論",
                    "category": CourseCategory.SOPHOMORE,
                },
                {
                    "name": "作業系統概論",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "機器學習概論",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "人工智慧總整與實作",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "網路程式設計概論",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "電腦安全總整與實作",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "計算機圖學概論",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "影像處理概論",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "網路系統總整與實作",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "編譯器設計概論",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "微處理機系統原理與實作",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "微處理機系統實驗",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "嵌入式系統總整與實作",
                    "category": CourseCategory.JUNIOR
                },
                {
                    "name": "企業網路安全",
                    "category": CourseCategory.JUNIOR,
                },
                {
                    "name": "多媒體資訊系統概論",
                    "category": CourseCategory.JUNIOR,
                },
                {
                    "name": "軟體工程概論",
                    "category": CourseCategory.JUNIOR,
                },
                {
                    "name": "網路規劃與管理實務",
                    "category": CourseCategory.JUNIOR,
                },
                {
                    "name": "多媒體與人機互動總整與實作",
                    "category": CourseCategory.SENIOR
                },
                {
                    "name": "計算機系統管理",
                    "category": CourseCategory.SENIOR,
                },
                {
                    "name": "計算機網路管理",
                    "category": CourseCategory.SENIOR,
                },
                {
                    "name": "作業系統總整與實作",
                    "category": CourseCategory.SENIOR,
                },
                {
                    "name": "密碼工程",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "高等 UNIX 程式設計",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "計算機網路(研)",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "演算法(研)",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "網路程式設計(研)",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "網路安全",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "演化計算",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "視訊壓縮",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "圖形理論",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "計算機架構",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "分散式演算法",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "圖形識別",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "資料探勘",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "作業系統",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "編譯器設計",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "影像處理",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "計算機圖學",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "正規語言",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "軟體測試",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "無線網路",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "容錯計算",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "網路安全實務-攻擊與防禦",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "深度學習與實務",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "賽局理論及應用",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "電腦對局理論",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "生醫資料探勘",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "嵌入式即時系統",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "計算機系統安全",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "計算機網路安全",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "軟體工程",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "軟體架構",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "組合語言與系統程式",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "電腦安全概論",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "物聯網概論",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "嵌入式系統設計(研)",
                    "category": CourseCategory.GRADUATE,
                },
                {
                    "name": "電子學(一)",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "電路與電子學(一)",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "電路與電子學(二)",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "分析導論(一)",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "微分方程",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "有機化學(二)",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "基礎圖論",
                    "category": CourseCategory.INTERDISCIPLINARY,
                },
                {
                    "name": "音樂理論導論",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "統計學",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "經濟學概論",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "全球化與兩岸關係",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "地球科學概論",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "日本文化論",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "營建管理",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "法學緒論",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "財務管理",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "伊斯蘭文明",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "投資學",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "會計學(一)",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "會計學(二)",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "財務工程導論",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "普通心理學",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "統計學(一)",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "統計學(二)",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "邏輯學",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "日文(二)",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "期貨與選擇權",
                    "category": CourseCategory.GENERAL,
                },
                {
                    "name": "公司法",
                    "category": CourseCategory.GENERAL,
                },
            ]

            initial_courses = [
                Course(
                    name=unicodedata.normalize("NFKC", data["name"]),
                    category=data["category"],
                )
                for data in initial_courses_data
            ]
            session.add_all(initial_courses)
            await session.commit()

        result = await session.execute(select(func.count()).select_from(Meme))
        count = result.scalar()
        if count == 0:
            initial_memes = [
                Meme(
                    content="""#!/bin/bash

# Finals Week
while true; do
  if [ "$(coffee_level)" -lt 50 ]; then
    echo "CRITICAL: Coffee low!"
    make_coffee
  fi
done""",
                    language="bash",
                ),
                Meme(
                    content="""while (!coffee) {
  printf("Need more C0FF33\\n");
  productivity--;
  stress++;
}""",
                    language="c",
                ),
                Meme(
                    content="""# Python developers be like
import solution
from stackoverflow import code

def actual_work():
    pass  # TODO: Implement later""",
                    language="python",
                ),
                Meme(
                    content="""try {
  life();
} catch (err) {
  coffee.drink();
  life.retry();
}""",
                    language="javascript",
                ),
                Meme(
                    content="""/* CSS: The blessing and curse */
#submit-button {
  display: block;
  margin: 0 auto;
  position: relative !important;
  z-index: 999; /* Please work */
}""",
                    language="css",
                ),
                Meme(
                    content="""// 99 bugs in the code
// Take one down, patch it around
// 127 bugs in the code""",
                    language="javascript",
                ),
                Meme(
                    content="""def time_estimate(task):
    \"\"\"Estimates completion time\"\"\"
    realistic = calculate_hours(task)
    return realistic * 3  # Developer's constant""",
                    language="python",
                ),
                Meme(
                    content="""if (brain.available()) {
  code.write();
} else {
  coffee.consume();
}""",
                    language="javascript",
                ),
                Meme(
                    content="""class Student {
  constructor() {
    this.sleep = 0;
    this.stress = 100;
  }
}""",
                    language="javascript",
                ),
                Meme(
                    content="""SELECT motivation
FROM student
WHERE deadline < CURRENT_DATE
AND hours_slept > 3
-- Returns empty set""",
                    language="sql",
                ),
                Meme(
                    content="""const examTime = () => {
  panic();
  cram();
  return "Somehow passed";
};""",
                    language="javascript",
                ),
                Meme(
                    content="""fn main() {
    let code_quality = 100;
    let deadline = true;
    
    if deadline {
        println!("Who needs clean code anyway?");
        code_quality -= 80;
    }
}""",
                    language="rust",
                ),
                Meme(
                    content="""switch (mood) {
  case "happy": 
    code.works();
    break;
  default: // 99% of the time
    code.breaks();
}""",
                    language="javascript",
                ),
                Meme(
                    content="""class MyCat < Pet
  def initialize
    @helps_coding = false
  end
  
  def sit_on_keyboard
    puts "kjasdhIHDIhaoiy87yh" # Commit this
  end
end""",
                    language="ruby",
                ),
                Meme(
                    content="""function sleep() {
  return new Promise((resolve) => {
    // Never resolves for CS students
  });
}""",
                    language="javascript",
                ),
                Meme(
                    content="""<!-- Types of HTML elements -->
<div>What I wanted</div>
<div style="position:absolute;top:-500px;">
  What the designer wanted
</div>
<marquee>What the client asked for</marquee>""",
                    language="html",
                ),
                Meme(
                    content="""#include <iostream>

void debugCode() {
  std::cout << "This should work..." << std::endl;
  std::cout << "WHY doesn't it work?" << std::endl;
  std::cout << "Oh, semicolon missing" << std::endl;
}""",
                    language="cpp",
                ),
                Meme(
                    content="""<?php
// The official debugging technique
@$result = dangerous_function();
echo $result ?? "It broke again!";
// Add more @ symbols until it works
?>""",
                    language="php",
                ),
                Meme(
                    content="""// Types of errors:
// 1. Syntax errors
// 2. Logic errors 
// 3. "It worked on my machine" errors""",
                    language="javascript",
                ),
                Meme(
                    content="""fun main() {
    val states = listOf("It works!", "It doesn't work", "WHY doesn't it work??")
    println("Current: \${states.random()}")
}""",
                    language="kotlin",
                ),
                Meme(
                    content="""// Found in production code:
// Dear future me,
// I am sorry.
// Sincerely, past me.""",
                    language="javascript",
                ),
                Meme(
                    content="""let motivation = new Promise((resolve) => {
  setTimeout(resolve, Infinity);
  // Pending since 2020
});""",
                    language="javascript",
                ),
                Meme(
                    content="""-- SQL: Debugging in production
BEGIN TRANSACTION;
UPDATE users SET admin = TRUE;
-- TODO: Add WHERE clause
-- ...forgot to add it
COMMIT;""",
                    language="sql",
                ),
                Meme(
                    content="""function estimateProjectTime(hours) {
  return hours * 3; // The developer's constant
}""",
                    language="javascript",
                ),
            ]
            session.add_all(initial_memes)
            await session.commit()

async def get_session():
    """
    Database dependency for FastAPI endpoints.
    """
    async with AsyncSessionLocal() as session:
        yield session