import fs from 'fs/promises';
import path from 'path';


export async function getAssetFileTxt(category: string, filename: string): Promise<string> {
  const filePath = path.join(process.cwd(), 'assets',category, filename);
  return getTxtFile(filePath)
}


export async function getAssetFileBinary(category: string, filename: string): Promise<Buffer | null> {
  const filePath = path.join(process.cwd(), 'assets',category, filename);
  return getBinaryFile(filePath)
}



export async function getTxtFile(filePath: string): Promise<string> {
  const data = await fs.readFile(filePath, 'utf-8');
  return data;
}

export async function getBinaryFile(filePath: string): Promise<Buffer | null> {
  try {
    const data = await fs.readFile(filePath);
    return data;
  } catch {
     return null;
  }
}

export function generateRandomName(): string {
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let result = "";
  for (let i = 0; i < 6; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return result;
}