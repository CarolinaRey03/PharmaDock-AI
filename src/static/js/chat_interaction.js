/**
 * Handles key press events in the chat input field.
 * Triggers message sending when Enter is pressed.
 *
 * @param {Event} event - The keyboard event
 */
function handleKeyPress(event) {
  if (event.key === "Enter") {
    sendMessage();
  }
}

/**
 * Processes and sends the user message to the backend.
 * Displays user message, shows loading indicator, processes the response,
 * and renders the assistant's reply with markdown support.
 * Initializes molecular viewer when docking results are available.
 */
function sendMessage() {
  let input = document.getElementById("chatInput");
  let messageText = input.value.trim();

  if (messageText == "") {
    return;
  }

  let chatBox = document.getElementById("messages");
  chatBox.innerHTML += `<div class="text-end"><span class="badge chat-message user-message">${messageText}</span></div>`;

  let loadingId = `loading-${Date.now()}`;
  chatBox.innerHTML += `<div id="${loadingId}" class="text-start">
    <span class="badge bg-light text-dark p-2 loading-text d-inline-flex align-items-center">
      ${loadingMessage}
      <div class="spinner-border spinner-border-sm ms-2" role="status">
        <span class="visually-hidden">${loadingMessage}</span>
      </div>
    </span>
  </div>`
  chatBox.scrollTop = chatBox.scrollHeight;

  fetch("/chat/message/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCSRFToken(),
    },
    body: JSON.stringify({
      user_prompt: messageText,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      document.getElementById(loadingId).remove();

      if (data.error) {
        console.log("error")
        chatBox.innerHTML += `<div class="text-start"><div class="badge bg-danger p-2 chat-message">Error: ${data.error}</div></div>`;
        return
      }
      try {
        console.log("Response received:", data.content);

        let markdownConverter = new showdown.Converter({
          tables: true,
          tasklists: true,
          strikethrough: true,
          emoji: true,
          simplifiedAutoLink: true
        });

        let responseHTML = markdownConverter.makeHtml(data.content);

        let messageHTML = `
        <div class="text-start message-wrapper">
          <div class="markdown-content chat-bubble bot-message">
            ${responseHTML}
            ${data.docking_result_log ?
            `<div class="mt-3 text-center">
                <button class="btn btn-sm btn-primary" onclick="downloadDockingLog('${data.docking_result_log}')">
                  <i class="fas fa-download me-1"></i> ${downloadMessage}
                </button>
              </div>`
            : ''}
          </div>
        </div>`;

        chatBox.innerHTML += messageHTML;

        if (data.receptor_file && data.ligand_file && data.pos_file) {
          initializeMoleculeViewer(data.receptor_file, data.ligand_file, data.pos_file);
        }

      } catch (e) {
        console.error("Error procesando Markdown:", e);
        chatBox.innerHTML += `<div class="text-start"><div class="badge bg-secondary chat-message">${data.content}</div></div>`;
      }
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch((error) => {
      document.getElementById(loadingId).remove();
      console.error("Error:", error);
      chatBox.innerHTML += `<div class="text-start"><span class="badge bg-danger p-2">${serverErrorMessage} ${error.message}</span></div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    });

  input.value = "";
}

/**
 * Initializes the 3D molecular viewer with receptor and ligand data.
 * Fetches molecule data from server, renders them with 3DMol.js,
 * and handles loading states with visual transitions.
 *
 * @param {string} receptorPath - Server path to receptor molecule file
 * @param {string} ligandPath - Server path to ligand molecule file
 */
function initializeMoleculeViewer(receptorPath, ligandPath, posPath) {
  const viewerElement = document.getElementById('container-01');
  if (!viewerElement) {
    console.error("Element #container-01 not found");
    return;
  }

  // Clear any previous content
  viewerElement.innerHTML = '';

  // Make sure the container is visible
  viewerElement.style.display = "block";
  viewerElement.style.transform = "none";

  try {
    let viewer = $3Dmol.createViewer(viewerElement, {
      backgroundColor: 'white',
      width: viewerElement.offsetWidth || 500,
      height: viewerElement.offsetHeight || 400
    });

    // Loading overlay to show while fetching data
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'loading-overlay';
    loadingOverlay.innerHTML = `
      <div class="loading-content">
        <div class="spinner-border text-light" role="status"></div>
        <p class="mt-2">Cargando visualización...</p>
      </div>
    `;
    viewerElement.appendChild(loadingOverlay);

    Promise.all([
      fetch(`/chat/get-docking-file/${receptorPath}`)
        .then(response => {
          if (!response.ok) throw new Error(`HTTP error ${response.status}`);
          return response.text();
        }),
      fetch(`/chat/get-docking-file/${ligandPath}`)
        .then(response => {
          if (!response.ok) throw new Error(`HTTP error ${response.status}`);
          return response.text();
        }),
      fetch(`/chat/get-docking-file/${posPath}`)
        .then(response => {
          if (!response.ok) throw new Error(`HTTP error ${response.status}`);
          return response.text();
        })
    ])
      .then(([receptorData, ligandData, posData]) => {
        if (!receptorData || receptorData.length < 10) {
          throw new Error("Invalid receptor data");
        }
        if (!posData || posData.length < 10) {
          throw new Error("Invalid ligand position data");
        }
        if (!ligandData || ligandData.length < 10) {
          throw new Error("Invalid ligand data");
        }

        viewer.addModel(receptorData, 'pdbqt');
        viewer.addModel(ligandData, 'sdf');
        viewer.addModel(posData, 'pdbqt')
        viewer = get3DMolStyle(viewer);
        viewer.zoomTo();
        viewer.render();

        // Fade out the loading overlay
        setTimeout(() => {
          loadingOverlay.classList.add('fade-out');
          setTimeout(() => {
            if (loadingOverlay.parentNode) {
              loadingOverlay.parentNode.removeChild(loadingOverlay);
            }
          }, 500);

          viewerElement.style.transition = "opacity 0.8s ease, transform 0.8s ease";
          viewerElement.style.opacity = "1";
          viewerElement.style.transform = "translateY(0)";
          viewerElement.classList.add('active');

          // Resize to make sure everything fits properly
          setTimeout(() => {
            viewer.resize();
            viewer.render();
          }, 100);
        }, 800);
      })
      .catch(error => {
        console.error("Error loading molecules:", error);
        viewerElement.innerHTML = `
        <div class="alert alert-danger m-3">
          ${loadingErrorMessage} ${error.message}
        </div>`;
      });
  } catch (e) {
    console.error("Error creating viewer:", e);
    viewerElement.innerHTML = `
      <div class="alert alert-danger m-3">
        Error creating viewer: ${e.message}
      </div>`;
  }
}

/**
 * Downloads docking log file from the server.
 * Creates a temporary anchor element to trigger the download.
 *
 * @param {string} logPath - Server path to the docking log file
 */
function downloadDockingLog(logPath) {
  const logUrl = `/chat/get-docking-log/${logPath}`

  const downloadLink = document.createElement('a')
  downloadLink.href = logUrl

  const fileName = logPath.split('/').pop()
  downloadLink.download = fileName

  document.body.appendChild(downloadLink)
  downloadLink.click()
  document.body.removeChild(downloadLink)
}

/**
 * Retrieves the CSRF token from cookies for secure requests.
 *
 * @returns {string} The CSRF token value
 */
function getCSRFToken() {
  let cookieValue = null;
  let cookies = document.cookie.split(";")
  for (let i = 0; i < cookies.length; i++) {
    let cookie = cookies[i].trim()
    if (cookie.startsWith("csrftoken=")) {
      cookieValue = cookie.substring("csrftoken=".length, cookie.length)
      break
    }
  }
  return cookieValue
}
