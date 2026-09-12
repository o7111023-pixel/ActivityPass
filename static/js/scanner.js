(() => {
  const start = document.getElementById('start-scanner');
  const stop = document.getElementById('stop-scanner');
  const video = document.getElementById('scanner-video');
  const message = document.getElementById('scanner-message');
  const form = document.getElementById('scanner-form');
  const input = document.getElementById('scanner-code');
  let controls = null;

  if (!start || !stop || !video || !message || !form || !input) return;
  if (!window.ZXingBrowser) {
    message.textContent = 'Camera scanner is unavailable. Enter the pass code manually.';
    return;
  }

  start.addEventListener('click', async () => {
    try {
      const reader = new ZXingBrowser.BrowserMultiFormatReader();
      message.textContent = 'Point the camera at the QR or barcode…';
      controls = await reader.decodeFromVideoDevice(undefined, video, (result) => {
        if (result) {
          input.value = result.getText();
          stopScanner();
          form.submit();
        }
      });
    } catch (error) {
      message.textContent = 'Camera could not start. Use HTTPS/localhost and allow camera access.';
    }
  });

  function stopScanner() {
    if (controls) { controls.stop(); controls = null; }
    if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
  }

  stop.addEventListener('click', stopScanner);
})();
