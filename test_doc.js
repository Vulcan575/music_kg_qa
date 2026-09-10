// 简单的文档生成测试
const { Document, Packer, Paragraph, TextRun } = require("docx");
const fs = require("fs");

const outputDir = "C:\\Users\\Tina\\Desktop\\hjh毕设\\chapters_docx";

// 确保输出目录存在
if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
    console.log("创建目录:", outputDir);
}

// 创建一个简单的测试文档
const doc = new Document({
    sections: [{
        properties: {},
        children: [
            new Paragraph({
                children: [
                    new TextRun({
                        text: "第一章 绪论",
                        bold: true,
                        size: 48,
                    }),
                ],
                alignment: "center",
            }),
            new Paragraph({
                children: [
                    new TextRun({
                        text: "测试内容",
                        size: 24,
                    }),
                ],
            }),
        ],
    }],
});

// 生成文档
Packer.toBuffer(doc).then(buffer => {
    const filePath = outputDir + "\\第一章_绪论.docx";
    fs.writeFileSync(filePath, buffer);
    console.log("✓ 已生成测试文档:", filePath);
}).catch(err => {
    console.error("生成失败:", err);
});
