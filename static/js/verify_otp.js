function verifyOTP(){

    let otp=document.getElementById("otp").value;

    fetch("/verify-otp",{

        method:"POST",

        headers:{
            "Content-Type":"application/x-www-form-urlencoded"
        },

        body:"otp="+otp

    })

    .then(res=>res.json())

    .then(data=>{

        let status=document.getElementById("otp-status");

        if(data.success){

            status.innerHTML="✔ OTP Verified";
            status.className="success";

            document.getElementById("password-section").style.display="block";

        }

        else{

            status.innerHTML="✖ Invalid OTP";
            status.className="error";

        }

    });

}