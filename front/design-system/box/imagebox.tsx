export default function ImageBox({
  src,
  label,
  onClick,
  className = 'max-h-[40vh] max-w-full h-auto w-auto object-contain'
}: {
  src: string;
  label: string;
  onClick: () => void;
  className? : string;
}) {
  return (
    <div className="flex flex-col items-center w-full h-full">
      <div
        className="w-full h-full border rounded overflow-hidden bg-black cursor-pointer"
        onClick={onClick}
      >
        <img src={src} alt={label} className={className} />
      </div>
      <p className="mt-2 text-center text-sm text-gray-600">{label}</p>
    </div>
  );
}