import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "E:/ai_company_faz12.1/outputs/019f8bbf-d286-7153-9998-9002fd6ab9a9";
const previewRoot = path.join(root, "previews");
await fs.mkdir(previewRoot, { recursive: true });
const logLines = [];
const record = (...parts) => logLines.push(parts.join(" "));

const inputs = [
  {
    key: "student_tracking",
    file: path.join(root, "Edanur_Ogrenci_Takip_Sistemi_export.xlsx"),
    sheets: [
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
    ],
  },
  {
    key: "lesson_form_responses",
    file: path.join(root, "dersplani_etablo_export.xlsx"),
    sheets: ["Sayfa1"],
  },
];

for (const input of inputs) {
  const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(input.file));
  const overview = await workbook.inspect({
    kind: "workbook,sheet,table,definedName,drawing",
    maxChars: 12000,
    tableMaxRows: 8,
    tableMaxCols: 12,
    tableMaxCellChars: 120,
  });
  record(`=== ${input.key}: OVERVIEW ===`);
  record(overview.ndjson);

  const formulas = await workbook.inspect({
    kind: "formula",
    maxChars: 12000,
    options: { maxResults: 300 },
  });
  record(`=== ${input.key}: FORMULAS ===`);
  record(formulas.ndjson);

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!",
    options: { useRegex: true, maxResults: 300 },
    summary: "formula error scan",
  });
  record(`=== ${input.key}: ERRORS ===`);
  record(errors.ndjson);

  for (const sheetName of input.sheets) {
    const region = await workbook.inspect({
      kind: "region",
      sheetId: sheetName,
      maxChars: 8000,
      tableMaxRows: 30,
      tableMaxCols: 20,
      tableMaxCellChars: 140,
    });
    record(`=== ${input.key}: REGION ${sheetName} ===`);
    record(region.ndjson);

    const preview = await workbook.render({
      sheetName,
      autoCrop: "all",
      scale: 1,
      format: "png",
    });
    const safeName = sheetName.replaceAll(/[<>:"/\\|?*]/g, "_");
    await fs.writeFile(
      path.join(previewRoot, `${input.key}__${safeName}.png`),
      new Uint8Array(await preview.arrayBuffer()),
    );
  }
}

await fs.writeFile(path.join(root, "workbook_audit.ndjson"), logLines.join("\n"), "utf8");
console.log(`AUDIT_OK inputs=${inputs.length} previews=${inputs.reduce((sum, input) => sum + input.sheets.length, 0)}`);
