// 逐个生成文档
const { Document, Packer, Paragraph, TextRun, AlignmentType } = require("docx");
const fs = require("fs");

const outputDir = "C:\\Users\\Tina\\Desktop\\hjh毕设\\chapters_docx";

console.log("开始生成文档...");

async function genChapter1() {
    const doc = new Document({
        sections: [{
            children: [
                new Paragraph({
                    children: [new TextRun({ text: "第1章 绪论", bold: true, size: 48 })],
                    alignment: AlignmentType.CENTER
                }),
                new Paragraph({
                    children: [new TextRun({ text: "1.1 研究背景与意义", bold: true, size: 32 })]
                }),
                new Paragraph({
                    children: [new TextRun({ text: "音乐产业数字化转型正在深刻改变人们的文化消费方式。根据国际唱片业协会(IFPI)发布的《2024全球音乐报告》，2023年全球音乐流媒体收入达到787亿美元，同比增长11.2%，中国音乐市场收入位列全球第七。", size: 24 })]
                })
            ]
        }]
    });
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputDir + "\\第一章_绪论.docx", buf);
    console.log("第一章完成");
}

async function genChapter2() {
    const doc = new Document({
        sections: [{
            children: [
                new Paragraph({
                    children: [new TextRun({ text: "第2章 相关技术与理论基础", bold: true, size: 48 })],
                    alignment: AlignmentType.CENTER
                }),
                new Paragraph({
                    children: [new TextRun({ text: "2.1 Scrapy爬虫框架", bold: true, size: 32 })]
                }),
                new Paragraph({
                    children: [new TextRun({ text: "Scrapy是一个基于Python的高性能Web爬虫框架，采用异步非阻塞的Twisted网络库实现，能够高效地处理大量HTTP请求。", size: 24 })]
                })
            ]
        }]
    });
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputDir + "\\第二章_相关技术.docx", buf);
    console.log("第二章完成");
}

async function genChapter3() {
    const doc = new Document({
        sections: [{
            children: [
                new Paragraph({
                    children: [new TextRun({ text: "第3章 需求分析与总体设计", bold: true, size: 48 })],
                    alignment: AlignmentType.CENTER
                }),
                new Paragraph({
                    children: [new TextRun({ text: "3.1 需求分析", bold: true, size: 32 })]
                }),
                new Paragraph({
                    children: [new TextRun({ text: "本节通过用例分析明确系统应提供的功能需求，并分析系统的非功能需求约束。", size: 24 })]
                })
            ]
        }]
    });
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputDir + "\\第三章_需求分析与总体设计.docx", buf);
    console.log("第三章完成");
}

async function genChapter4() {
    const doc = new Document({
        sections: [{
            children: [
                new Paragraph({
                    children: [new TextRun({ text: "第4章 核心模块详细设计", bold: true, size: 48 })],
                    alignment: AlignmentType.CENTER
                }),
                new Paragraph({
                    children: [new TextRun({ text: "4.1 数据采集模块设计", bold: true, size: 32 })]
                }),
                new Paragraph({
                    children: [new TextRun({ text: "数据采集是构建知识图谱的基础。本课题的爬虫模块基于Scrapy框架实现。", size: 24 })]
                })
            ]
        }]
    });
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputDir + "\\第四章_核心模块详细设计.docx", buf);
    console.log("第四章完成");
}

async function genChapter5() {
    const doc = new Document({
        sections: [{
            children: [
                new Paragraph({
                    children: [new TextRun({ text: "第5章 系统实现与测试", bold: true, size: 48 })],
                    alignment: AlignmentType.CENTER
                }),
                new Paragraph({
                    children: [new TextRun({ text: "5.1 开发环境配置", bold: true, size: 32 })]
                }),
                new Paragraph({
                    children: [new TextRun({ text: "本系统的开发和运行环境配置如下：操作系统：Windows 11 64位；Python版本：Python 3.10。", size: 24 })]
                })
            ]
        }]
    });
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputDir + "\\第五章_系统实现与测试.docx", buf);
    console.log("第五章完成");
}

async function genChapter6() {
    const doc = new Document({
        sections: [{
            children: [
                new Paragraph({
                    children: [new TextRun({ text: "第6章 总结与展望", bold: true, size: 48 })],
                    alignment: AlignmentType.CENTER
                }),
                new Paragraph({
                    children: [new TextRun({ text: "6.1 研究工作总结", bold: true, size: 32 })]
                }),
                new Paragraph({
                    children: [new TextRun({ text: "本课题设计并实现了一个基于知识图谱与大模型的音乐领域智能问答系统。", size: 24 })]
                })
            ]
        }]
    });
    const buf = await Packer.toBuffer(doc);
    fs.writeFileSync(outputDir + "\\第六章_总结与展望.docx", buf);
    console.log("第六章完成");
}

async function main() {
    await genChapter1();
    await genChapter2();
    await genChapter3();
    await genChapter4();
    await genChapter5();
    await genChapter6();
    console.log("全部文档生成完成！");
}

main().catch(e => console.error("错误:", e));
