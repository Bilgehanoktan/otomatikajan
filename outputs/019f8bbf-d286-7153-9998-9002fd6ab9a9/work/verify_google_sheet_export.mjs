import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "E:/ai_company_faz12.1/outputs/019f8bbf-d286-7153-9998-9002fd6ab9a9";
const file = path.join(root, "Google_Form_Altyapisi_canli.xlsx");
const previewDir = path.join(root, "google_sheet_previews");
await fs.mkdir(previewDir, { recursive: true });

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(file));
const overview = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 9000,
  tableMaxRows: 10,
  tableMaxCols: 25,
});
const formulas = await workbook.inspect({
  kind: "formula",
  sheetId: "Aktarım Kontrolü",
  range: "A1:Y5",
  maxChars: 10000,
  options: { maxResults: 100 },
});
const setup = await workbook.inspect({
  kind: "table",
  sheetId: "Form Kurulum",
  range: "A1:G21",
  include: "values,formulas",
  maxChars: 9000,
  tableMaxRows: 25,
  tableMaxCols: 7,
});
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!",
  options: { useRegex: true, maxResults: 300 },
  summary: "live Google Sheet export formula error scan",
});
await fs.writeFile(
  path.join(root, "google_sheet_verification.ndjson"),
  [overview.ndjson, formulas.ndjson, setup.ndjson, errors.ndjson].join("\n"),
  "utf8",
);

const renderRanges = {
  "Form Yanıtları": "A1:P20",
  "Aktarım Kontrolü": "A1:Y20",
  "Öğrenciler": "A1:J15",
  "Form Kurulum": "A1:G21",
};

for (const [sheetName, range] of Object.entries(renderRanges)) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(
    path.join(previewDir, `${sheetName.replaceAll(/[<>:"/\\|?*]/g, "_")}.png`),
    new Uint8Array(await preview.arrayBuffer()),
  );
}

console.log("GOOGLE_SHEET_VERIFY_OK");
console.log(errors.ndjson);
