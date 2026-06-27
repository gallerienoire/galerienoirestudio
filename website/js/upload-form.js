/* Galerie Noire — Upload Form Handler */

document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('upload-form');
  const submitBtn = document.getElementById('submit-btn');
  const statusDiv = document.getElementById('form-status');

  /* ---- File Upload UX ---- */
  const fileInput = document.getElementById('roomPhoto');
  const uploadArea = document.getElementById('file-upload-area');
  const uploadText = document.getElementById('upload-text');
  const previewGrid = document.getElementById('preview-grid');

  if (uploadArea && fileInput) {
    uploadArea.addEventListener('click', function() {
      fileInput.click();
    });

    uploadArea.addEventListener('dragover', function(e) {
      e.preventDefault();
      uploadArea.style.borderColor = 'var(--brass-gold)';
      uploadArea.style.background = 'rgba(197, 165, 90, 0.05)';
    });

    uploadArea.addEventListener('dragleave', function() {
      uploadArea.style.borderColor = 'rgba(197, 165, 90, 0.2)';
      uploadArea.style.background = 'transparent';
    });

    uploadArea.addEventListener('drop', function(e) {
      e.preventDefault();
      uploadArea.style.borderColor = 'rgba(197, 165, 90, 0.2)';
      uploadArea.style.background = 'transparent';
      if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        updateFilePreviews(e.dataTransfer.files);
      }
    });

    fileInput.addEventListener('change', function() {
      if (fileInput.files.length) {
        updateFilePreviews(fileInput.files);
      }
    });
  }

  function updateFilePreviews(files) {
    if (!previewGrid) return;
    previewGrid.innerHTML = '';
    if (files.length === 0) return;

    if (uploadText) {
      uploadText.textContent = files.length === 1 ? files[0].name : files.length + ' photos selected';
    }

    Array.from(files).forEach(function(file) {
      const reader = new FileReader();
      reader.onload = function(e) {
        const div = document.createElement('div');
        div.style.cssText = 'aspect-ratio:1; overflow:hidden; border:1px solid rgba(197,165,90,0.15);';
        const img = document.createElement('img');
        img.src = e.target.result;
        img.style.cssText = 'width:100%; height:100%; object-fit:cover;';
        div.appendChild(img);
        previewGrid.appendChild(div);
      };
      reader.readAsDataURL(file);
    });
  }

  /* ---- Form Submission ---- */
  if (submitBtn) {
    submitBtn.addEventListener('click', submitForm);
  }

  async function submitForm() {
    if (!form) return;

    // Collect field values
    const name = form.querySelector('[name="name"]').value.trim();
    const email = form.querySelector('[name="email"]').value.trim();
    const tier = form.querySelector('[name="tier"]:checked');
    const roomType = form.querySelector('[name="roomType"]').value;
    const ceilingHeight = form.querySelector('[name="ceilingHeight"]').value;
    const roomWidth = form.querySelector('[name="roomWidth"]').value.trim();
    const roomLength = form.querySelector('[name="roomLength"]').value.trim();
    const naturalLight = form.querySelector('[name="naturalLight"]').value;
    const wallColor = form.querySelector('[name="wallColor"]').value.trim();
    const existingFurniture = form.querySelector('[name="existingFurniture"]').value.trim();
    const furnitureStyle = form.querySelector('[name="furnitureStyle"]').value;
    const pinterestUrl = form.querySelector('[name="pinterestUrl"]').value.trim();
    const favoriteSpaces = form.querySelector('[name="favoriteSpaces"]').value.trim();
    const roomVibe = form.querySelector('[name="roomVibe"]').value.trim();
    const photos = fileInput ? fileInput.files : [];

    // Validate required fields
    if (!email) {
      showStatus('Please enter your email address.', 'error');
      return;
    }
    if (!tier) {
      showStatus('Please select a pricing tier.', 'error');
      return;
    }

    // Show loading
    submitBtn.disabled = true;
    submitBtn.textContent = 'Submitting...';
    showStatus('Uploading your project...', 'info');

    // Build FormData
    const formData = new FormData();
    formData.append('email', email);
    formData.append('name', name || email.split('@')[0]);

    const tierValue = tier.value;
    formData.append('tier', tierValue);

    // Build metadata JSON
    const metadata = {
      roomType: roomType || '',
      ceilingHeight: ceilingHeight || '',
      roomWidth: roomWidth || '',
      roomLength: roomLength || '',
      naturalLight: naturalLight || '',
      wallColor: wallColor || '',
      existingFurniture: existingFurniture || '',
      furnitureStyle: furnitureStyle || '',
      pinterestUrl: pinterestUrl || '',
      favoriteSpaces: favoriteSpaces || '',
      roomVibe: roomVibe || ''
    };
    formData.append('metadata', JSON.stringify(metadata));

    // Append all selected photos
    for (let i = 0; i < photos.length; i++) {
      formData.append('roomPhoto', photos[i]);
    }

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.error || `Server error: ${response.status}`);
      }

      const result = await response.json();

      // Success — redirect
      window.location.href = '/success.html?project=' + encodeURIComponent(result.id) + '&tier=' + encodeURIComponent(tierValue);

    } catch (err) {
      showStatus(err.message || 'Something went wrong. Please try again.', 'error');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit My Room';
    }
  }

  function showStatus(message, type) {
    if (!statusDiv) return;
    statusDiv.innerHTML = '<p style="color:' + (type === 'error' ? '#e74c3c' : type === 'info' ? 'var(--warm-grey)' : 'var(--brass-gold)') + '; font-size:0.95rem;">' + escapeHtml(message) + '</p>';
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
});