document.addEventListener('DOMContentLoaded', function() {
    // Get today's date
    const today = new Date();
    const todayDate = today.toISOString().split('T')[0];
    
    // Set the default value for the date input
    document.getElementById('date').value = todayDate;
});