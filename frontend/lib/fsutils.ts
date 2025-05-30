import fs from 'fs/promises';
import path from 'path';


export async function getAssetFileTxt(catagory: string, filename: string): Promise<string> {
  const filePath = path.join(process.cwd(), 'assets',filename);
  const data = await fs.readFile(filePath, 'utf-8');
  return data;
}