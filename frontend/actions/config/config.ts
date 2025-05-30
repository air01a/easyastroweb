'use server';
import { getConfiguration } from "@/lib/config";

export const getConfig = async () => {
  return await getConfiguration();
}