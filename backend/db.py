from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from sqlmodel import select, func

from config import SQLALCHEMY_DATABASE_URL
from models import SQLModel, User, Archive, Meme, Course, CourseCategory, ArchiveType

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        result = await session.execute(select(func.count()).select_from(Course))
        count = result.scalar()
        if count == 0:
            initial_courses = [
                Course(
                    name="演算法",
                    category=CourseCategory.SOPHOMORE,
                ),
                Course(
                    name="作業系統",
                    category=CourseCategory.JUNIOR,
                ),
                Course(
                    name="計算機組織",
                    category=CourseCategory.SOPHOMORE,
                ),
            ]
        
            session.add_all(initial_courses)
            await session.commit()

        result = await session.execute(select(func.count()).select_from(Archive))
        count = result.scalar()
        if count == 0:
            sample_archives = [
                Archive(
                    name="演算法期中考 2024",
                    course_id=1,  # 演算法
                    academic_year=2024,
                    archive_type=ArchiveType.MIDTERM,
                    professor="黃凱揚",
                    has_answers=True,
                    pdf_object_name="samples/algo_mid_2024.pdf"
                ),
                Archive(
                    name="演算法期末考 2024",  # Add name
                    course_id=1,  # 演算法
                    academic_year=2024,  # Add academic_year
                    archive_type=ArchiveType.FINAL,
                    professor="黃凱揚",
                    has_answers=True,
                    pdf_object_name="samples/algo_final_2024.pdf"
                ),
                Archive(
                    name="演算法期末考 2023",  # Add name
                    course_id=1,  # 演算法
                    academic_year=2023,  # Add academic_year
                    archive_type=ArchiveType.FINAL,
                    professor="黃凱強",
                    has_answers=True,
                    pdf_object_name="samples/algo_final_2024.pdf"
                ),
                Archive(
                    name="演算法期末考 2024",  # Add name
                    course_id=1,  # 演算法
                    academic_year=2022,  # Add academic_year
                    year=2022,
                    archive_type=ArchiveType.QUIZ,
                    professor="黃凱揚",
                    has_answers=True,
                    pdf_object_name="samples/algo_final_2024.pdf"
                ),
                Archive(
                    name="作業系統期中考 2024",  # Add name
                    course_id=2,  # 作業系統
                    academic_year=2024,  # Add academic_year
                    archive_type=ArchiveType.MIDTERM,
                    professor="虞竹平",
                    has_answers=True,
                    pdf_object_name="samples/os_mid_2024.pdf"
                ),
          ]

            session.add_all(sample_archives)
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


async def get_db():
    """
    Database dependency for FastAPI endpoints.
    """
    async with AsyncSessionLocal() as session:
        yield session
