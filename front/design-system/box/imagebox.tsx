export default function ImageBox({
  src,
  label,
  onClick,
}: {
  src: string;
  label: string;
  onClick: () => void;
}) {
  return (
    <div className="flex flex-col items-center w-full">
      <div
        className="w-full h-64 border rounded overflow-hidden bg-black cursor-pointer"
        onClick={onClick}
      >
        <img src={src} alt={label} className="w-full h-full object-cover" />
      </div>
      <p className="mt-2 text-center text-sm text-gray-600">{label}</p>
    </div>
  );
}