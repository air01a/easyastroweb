import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";


export async function middleware(req: NextRequest) {
    console.log(req.nextUrl.pathname);
    if (!req.cookies.get('observerLocation') && !req.nextUrl.pathname.startsWith('/location')) {
        return NextResponse.redirect(new URL("/location", req.url));
    }
    return NextResponse.next();  
}

export const config = {
    matcher: [
    "/((?!_next|favicon.ico|static|robots.txt|sitemap.xml).*)", // Exclure _next et autres fichiers statiques
  ],
};