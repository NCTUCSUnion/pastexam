from sqlalchemy import text
from sqlmodel import select, func, SQLModel

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

        # Check and add initial memes
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