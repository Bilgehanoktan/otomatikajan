import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "E:/ai_company_faz12.1/outputs/019f8bbf-d286-7153-9998-9002fd6ab9a9";
const sourcePath = path.join(root, "Edanur_Ogrenci_Takip_Sistemi_export.xlsx");
const outputPath = path.join(root, "Edanur_Ogrenci_Takip_Sistemi_v4_2_4_Onarilmis.xlsx");
const previewDir = path.join(root, "repaired_previews");
await fs.mkdir(previewDir, { recursive: true });

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourcePath));
const main = workbook.worksheets.getItem("00_Ana");
const setup = workbook.worksheets.getItem("08_Google_Kurulum");

main.getRange("A1").values = [["EDANUR ÖĞRENCİ TAKİP SİSTEMİ v4.2.4 — 10 SAYFALIK SADE YAPI"]];

main.unmergeCells("A4:J4");
main.unmergeCells("F4:J4");
main.getRange("A4").values = [["KULLANIM SIRASI"]];
main.getRange("F4").values = [["SAYFA AZALTMA KARARI"]];
main.mergeCells("A4:D4");
main.mergeCells("F4:J4");

main.getRange("F12").values = [["TESLİM KARARI: FORM BAĞLANTISI BEKLİYOR"]];
main.getRange("F12:J12").format = {
  fill: "#FCE8B2",
  font: { bold: true, color: "#8A3B12" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};

main.getRange("E41:J43").values = [
  ["Form 8/15; bağlantı yok", "ENGELLENDİ", "Canlı Form + Drive araması", "Her revizyonda", "Kritik", "Form dosyası Drive'da görünmüyor"],
  ["Test çalıştırılamadı", "ENGELLENDİ", "Canlı Form + Drive araması", "Her revizyonda", "Kritik", "Form dosyası Drive'da görünmüyor"],
  ["Test çalıştırılamadı", "ENGELLENDİ", "Canlı Form + Drive araması", "Her revizyonda", "Kritik", "Form dosyası Drive'da görünmüyor"],
];
main.getRange("F41:F43").format = {
  fill: "#FCE8B2",
  font: { bold: true, color: "#8A3B12" },
  horizontalAlignment: "center",
};

main.getRange("A51:J51").copyFrom(main.getRange("A49:J49"), "all");
main.getRange("A51:J51").values = [[
  "T-27",
  "Dosya / Birleştirme",
  "sheet1.xml mergeCells çakışmasını tara.",
  "0 çakışma",
  "0 çakışma",
  "GEÇTİ",
  "00_Ana!A4:D4 ve F4:J4",
  "Her revizyonda",
  "Kritik",
  "A4:J4 kaldırıldı",
]];

setup.getRange("H26:H28").values = [["Tamamlandı"], ["ENGELLENDİ"], ["ENGELLENDİ"]];
setup.getRange("H27:H28").format = {
  fill: "#FCE8B2",
  font: { bold: true, color: "#8A3B12" },
  horizontalAlignment: "center",
};

const relevant = await workbook.inspect({
  kind: "table",
  sheetId: "00_Ana",
  range: "A1:J51",
  include: "values,formulas",
  maxChars: 14000,
  tableMaxRows: 55,
  tableMaxCols: 10,
});
const setupCheck = await workbook.inspect({
  kind: "table",
  sheetId: "08_Google_Kurulum",
  range: "A23:H33",
  include: "values,formulas",
  maxChars: 5000,
  tableMaxRows: 15,
  tableMaxCols: 8,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!",
  options: { useRegex: true, maxResults: 300 },
  summary: "final formula error scan",
});
await fs.writeFile(
  path.join(root, "repair_verification.ndjson"),
  [relevant.ndjson, setupCheck.ndjson, errors.ndjson].join("\n"),
  "utf8",
);

const sheetNames = [
  "00_Ana",
  "01_Panel_Program",
  "02_Öğrenciler",
  "03_Ders_Girişi",
  "04_Ödev_Konu",
  "05_Sınavlar",
  "06_Veli_Ödeme",
  "07_Google_Form",
  "08_Google_Kurulum",
  "09_Parametreler",
];

for (const sheetName of sheetNames) {
  const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  const safeName = sheetName.replaceAll(/[<>:"/\\|?*]/g, "_");
  await fs.writeFile(
    path.join(previewDir, `${safeName}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`REPAIR_OK output=${outputPath} previews=${sheetNames.length}`);
