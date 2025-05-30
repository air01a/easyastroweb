import { getAssetFileBinary } from "@/lib/fsutils";
import { NextResponse } from "next/server";
const GET = async (request: Request,
    {params}: { params: Promise<{ name:string }>}) => {
    const name = (await params).name;

    try {

    
        const image = await getAssetFileBinary('catalog', name);
        if (!image) {
            return new Response('Image not found', { status: 404 });
        }

        const ext = name.split('.').pop()?.toLowerCase();
        const mimeType = ext === 'png'
        ? 'image/png'
        : ext === 'jpg' || ext === 'jpeg'
        ? 'image/jpeg'
        : ext === 'webp'
        ? 'image/webp'
        : ext === 'gif'
        ? 'image/gif'
        : 'application/octet-stream';

        return new NextResponse(image, {
        status: 200,
        headers: {
            'Content-Type': mimeType,
            'Content-Disposition': `attachment; filename="${name}"`,
        },
        });
    } catch (error) {
        console.error('Error fetching image:', error);
        return new Response('Internal Server Error', { status: 500 });
    }
}

export {GET}