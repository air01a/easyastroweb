import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";


export async function middleware(req: NextRequest) {

    return NextResponse.next();  
}

export const config = {
    matcher: [
    "/((?!_next|favicon.ico|static|robots.txt|sitemap.xml).*)", // Exclure _next et autres fichiers statiques
  ],
};