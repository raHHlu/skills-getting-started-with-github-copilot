document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const cardTemplate = document.getElementById("activity-card-template");

  // helper to get display name and initials from a participant string
  function parseParticipant(raw) {
    // raw may be an object or string; handle common cases
    const name =
      typeof raw === "string"
        ? raw.includes("@")
          ? raw.split("@")[0].replace(/[._-]/g, " ")
          : raw
        : raw.name || String(raw);
    const parts = name.trim().split(/\s+/);
    const initials =
      parts.length === 1
        ? parts[0].slice(0, 2).toUpperCase()
        : (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    return { name, initials };
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message / existing cards
      activitiesList.innerHTML = "";

      // Reset select dropdown but keep the placeholder option
      if (activitySelect.options.length > 0) {
        // preserve first placeholder option
        const placeholder = activitySelect.options[0];
        activitySelect.innerHTML = "";
        activitySelect.appendChild(placeholder);
      }

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        // clone template
        const node = cardTemplate.content.cloneNode(true);
        const article = node.querySelector(".activity-card");
        const titleEl = node.querySelector(".activity-title");
        const metaEl = node.querySelector(".activity-meta");
        const descEl = node.querySelector(".activity-desc");
        const participantsList = node.querySelector(".participants-list");
        const emptyNote = node.querySelector(".empty-note");
        const participantsCount = node.querySelector(".participants-count");
        const participantsContainer = node.querySelector(".participants");
        const toggleCheckbox = node.querySelector(".participants-toggle-checkbox");

        titleEl.textContent = name;
        metaEl.textContent = `${details.instructor || "Instructor"} · ${details.schedule || "TBD"}`;
        descEl.textContent = details.description || "";

        const participants = Array.isArray(details.participants) ? details.participants : [];
        participantsCount.textContent = participants.length;

        if (participants.length === 0) {
          emptyNote.hidden = false;
        } else {
          emptyNote.hidden = true;
          participants.forEach((p) => {
            const { name: displayName, initials } = parseParticipant(p);
            const li = document.createElement("li");
            li.className = "participant";
            li.innerHTML = `<span class="avatar" aria-hidden="true">${initials}</span><span class="name">${displayName}</span>`;
            participantsList.appendChild(li);
          });
        }

        // show availability as small meta appended to metaEl
        const spotsLeft = (details.max_participants || 0) - participants.length;
        const avail = document.createElement("div");
        avail.className = "activity-availability";
        avail.textContent = `${spotsLeft} spots left`;
        metaEl.appendChild(document.createTextNode(" "));
        metaEl.appendChild(avail);

        // start collapsed; toggle will reveal participants
        if (participantsContainer) {
          participantsContainer.hidden = true;
        }
        if (toggleCheckbox) {
          toggleCheckbox.checked = false;
          toggleCheckbox.addEventListener("change", () => {
            participantsContainer.hidden = !toggleCheckbox.checked;
            // keep simple accessible label change
            const label = node.querySelector(".toggle-label");
            if (label) label.textContent = toggleCheckbox.checked ? "Hide participants" : "Show participants";
          });
        }

        activitiesList.appendChild(node);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message || "Signed up successfully";
        messageDiv.classList.remove("error");
        messageDiv.classList.add("success");
        signupForm.reset();

        // Refresh activities to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.classList.remove("success");
        messageDiv.classList.add("error");
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.classList.remove("success");
      messageDiv.classList.add("error");
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
