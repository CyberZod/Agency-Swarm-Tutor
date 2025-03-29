import asyncio
from UploadTool import UploadToOpenAITool  # Adjust the import path if needed

async def test_upload():
    tool = UploadToOpenAITool()
    result = await tool.run()
    print(result)

if __name__ == "__main__":
    asyncio.run(test_upload())
