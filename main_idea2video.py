import asyncio
from pipelines.idea2video_pipeline import Idea2VideoPipeline


# SET YOUR OWN IDEA, USER REQUIREMENT, AND STYLE HERE
idea = \
"""
A retired teacher in rural India learns coding at age 65 to build an educational app 
for underprivileged children. Despite struggles with technology and doubt from family, 
she perseveres. Six months later, her app reaches 10,000 students, 
and she becomes a local hero.
"""
user_requirement = \
"""
Inspirational tone for general audience. 4 scenes. 
5-7 shots per scene. Include wide establishing shots and emotional moments.
"""
style = "Documentary realism, natural lighting, warm color grading, intimate camera angles"



async def main():
    pipeline = Idea2VideoPipeline.init_from_config(config_path="configs/idea2video.yaml")
    await pipeline(idea=idea, user_requirement=user_requirement, style=style)

if __name__ == "__main__":
    asyncio.run(main())
