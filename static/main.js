console.log('HAPPY PET loaded');
const reserveForm = document.getElementById('reserveForm');
if(reserveForm){
  reserveForm.addEventListener('submit', function(e){
    const date = this.querySelector('input[name=date]').value;
    const time = this.querySelector('input[name=time]').value;
    if(!date || !time) return;
    const dt = new Date(date + 'T' + time);
    const now = new Date();
    if(dt < now){
      e.preventDefault();
      alert('Seleccione una fecha y hora futuras');
    }
  });
}
