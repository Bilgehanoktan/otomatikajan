import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "E:/ai_company_faz12.1/outputs/019f8bbf-d286-7153-9998-9002fd6ab9a9";
const file = path.join(root, "Edanur_Ogrenci_Takip_Sistemi_v4_2_4_Onarilmis.xlsx");
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(file));

const overview = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 7000,
  tableMaxRows: 6,
  tableMaxCols: 10,
});
const main = await workbook.inspect({
  kind: "table",
  sheetId: "00_Ana",
  range: "A1:J51",
  include: "values,formulas",
  maxChars: 14000,
  tableMaxRows: 55,
  tableMaxCols: 10,
});
const setup = await workbook.inspect({
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
  summary: "reimported formula error scan",
});

await fs.writeFile(
  path.join(root, "reimport_verification.ndjson"),
  [overview.ndjson, main.ndjson, setup.ndjson, errors.ndjson].join("\n"),
  "utf8",
);

console.log("REIMPORT_VERIFY_OK");
console.log(errors.ndjson);
