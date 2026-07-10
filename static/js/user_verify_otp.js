function verifyUserOTP() {
    let otp = document.getElementById("otp").value;
    fetch("/user-verify-otp", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: "otp=" + otp
    })
        .then(res => res.json())
        .then(data => {
            let status = document.getElementById("otp-status");
            if (data.success) {
                status.innerHTML = "✔ OTP Verified";
                status.style.color = "var(--sc-success)";
                document.getElementById("password-section").style.display = "block";
            } else {
                status.innerHTML = "✖ Invalid OTP";
                status.style.color = "var(--sc-danger)";
            }
        });
}
