


    
import { useEffect, useState } from 'react';
import { apiService } from "../../api/api";
import  Button  from "../../design-system/buttons/main";
import Swal from "sweetalert2";


export default function RunningPlanPage() {
   

  const [image1, setImage1] = useState<string | null>(null);
  const [image2, setImage2] = useState<string | null>(null);

  useEffect(() => {
    // Remplace les URL par tes vrais endpoints
    const baseUrl = apiService.getBaseUrl();
    fetch(`${baseUrl}/observation/last_stacked_image`)
      .then(res => res.blob())
      .then(blob => setImage1(URL.createObjectURL(blob)));

    fetch(`${baseUrl}/observation/last_stacked_image`)
      .then(res => res.blob())
      .then(blob => setImage2(URL.createObjectURL(blob)));
  }, []);


  const handleClick = () => {
    Swal.fire({
          title: "Are you sure?",
          text: "You won't be able to revert this!",
          icon: "warning",
          showCancelButton: true,
          confirmButtonColor: "#3085d6",
          cancelButtonColor: "#d33",
          confirmButtonText: "Yes, stop it!"
        }).then((result) => {        
          if (result.isConfirmed) {
            apiService.stopPlan();
          }
        });
    }



  return (
        <div className="flex flex-col md:flex-row gap-4 p-4">
      {image1 && (
        <div className="flex flex-col items-center w-full md:w-1/2">
          <img
            src={image1}
            alt="Image 1"
            className="w-full object-contain border rounded"
          />
          <p className="mt-2 text-center text-sm text-gray-600">Last stacked image</p>
        </div>
      )}
      {image2 && (
        <div className="flex flex-col items-center w-full md:w-1/2">
          <img
            src={image2}
            alt="Image 2"
            className="w-full object-contain border rounded"
          />
          <p className="mt-2 text-center text-sm text-gray-600">Last image taken</p>
        </div>
      )}
      <Button onClick={handleClick}>Stop plan</Button>
    </div>
  );
};
