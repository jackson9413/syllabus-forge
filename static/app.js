/* Syllabus Forge - vanilla JS front end */
(function () {
  "use strict";

  var $ = function (sel) { return document.querySelector(sel); };
  var state = { result: null, samples: [], runs: [] };

  function esc(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function setStatus(text) { $("#status").textContent = text; }

  function toast(message) {
    var el = document.createElement("div");
    el.className = "toast";
    el.textContent = message;
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 2600);
  }

  function scoreClass(value) {
    if (value >= 85) return "good";
    if (value >= 60) return "mid";
    return "bad";
  }

  function barColor(value) {
    if (value >= 85) return "var(--good)";
    if (value >= 60) return "var(--medium)";
    return "var(--critical)";
  }

  function render(result) {
    state.result = result;
    var meta = result.meta || {};
    var score = result.score || {};
    var axes = score.axes || {};
    var bits = [meta.code, meta.term, meta.level].filter(Boolean).join(" | ");
    var facts = [];
    if (meta.credits) facts.push(meta.credits + " credits");
    if (meta.weeks) facts.push(meta.weeks + " weeks");
    if (meta.meetings_per_week) {
      facts.push(meta.meetings_per_week + "x" + (meta.minutes_per_meeting || 50) + "min");
    }
    if (meta.students) facts.push(meta.students + " students");

    var html = '<div class="score-head">';
    html += '<div><div class="score-num ' + scoreClass(score.overall) + '">' + score.overall + '</div>';
    html += '<div class="verdict">' + esc((score.verdict || "").replace(/_/g, " ")) + '</div></div>';
    html += '<div><div class="meta-line">' + esc(meta.course || "Untitled course") + '</div>';
    html += '<div class="meta-line">' + esc(bits) + (bits && facts.length ? " &middot; " : "") + esc(facts.join(" &middot; ")) + '</div>';
    html += '<div class="meta-line">' + result.totals.critical + " critical / " + result.totals.high +
            " high / " + result.totals.medium + " medium / " + result.totals.low + " low findings</div></div>';
    html += '</div>';

    html += '<div class="axes">';
    Object.keys(axes).forEach(function (key) {
      var axis = axes[key];
      html += '<div class="axis-row"><div class="axis-name">' + esc(axis.label) +
              ' <span style="opacity:.6">(' + axis.weight + '%)</span></div>' +
              '<div class="bar"><i style="width:' + axis.score + '%;background:' + barColor(axis.score) + '"></i></div>' +
              '<div class="axis-val">' + axis.score + '</div></div>';
    });
    html += '</div>';

    if ((result.caps || []).length) {
      html += '<div class="caps"><h4>Structural caps applied</h4><ul>';
      result.caps.forEach(function (cap) {
        html += '<li><b>' + esc(cap.axis) + '</b> capped at ' + cap.cap + ' &mdash; ' + esc(cap.reason) + '</li>';
      });
      html += '</ul></div>';
    }

    var findings = result.findings || [];
    html += '<h3 class="sec">Findings (' + findings.length + ')</h3>';
    if (!findings.length) {
      html += '<p class="meta-line">No findings. The brief is clean on every axis checked.</p>';
    }
    findings.forEach(function (f) {
      html += '<div class="finding ' + esc(f.severity) + '">';
      html += '<h4><span class="sev ' + esc(f.severity) + '">' + esc(f.severity.toUpperCase()) + '</span>' +
              esc(f.title) + '</h4>';
      html += '<p class="lbl"><b>Evidence:</b> ' + esc(f.evidence) + '</p>';
      html += '<p class="lbl"><b>Why it matters:</b> ' + esc(f.why) + '</p>';
      html += '<p class="lbl"><b>Fix:</b> ' + esc(f.fix) + '</p>';
      html += '</div>';
    });

    var plan = result.fix_plan || [];
    if (plan.length) {
      html += '<h3 class="sec">Prioritised fix plan</h3><table><thead><tr><th>#</th><th>Fix</th>' +
              '<th>Severity</th><th>Est. gain</th></tr></thead><tbody>';
      plan.forEach(function (step, index) {
        html += '<tr><td>' + (index + 1) + '</td><td>' + esc(step.fix) + '</td><td>' +
                '<span class="sev ' + esc(step.severity) + '">' + esc(step.severity.toUpperCase()) + '</span></td>' +
                '<td>+' + step.estimated_score_gain + '</td></tr>';
      });
      html += '</tbody></table>';
    }

    var coverage = result.coverage || [];
    if (coverage.length) {
      html += '<h3 class="sec">Objective coverage</h3><table><thead><tr><th>#</th><th>Objective</th>' +
              '<th>Taught</th><th>Assessed by</th></tr></thead><tbody>';
      coverage.forEach(function (c) {
        html += '<tr><td>' + c.id + '</td><td>' + esc(c.text) + '</td><td>' +
                (c.taught_weeks.length ? esc(c.taught_weeks.join(", ")) : '<span class="chip bad">never</span>') +
                '</td><td>' +
                (c.assessed_by.length ? esc(c.assessed_by.join(", ")) +
                  (c.inferred ? ' <span class="chip">inferred</span>' : "") :
                  '<span class="chip bad">never</span>') + '</td></tr>';
      });
      html += '</tbody></table>';
    }

    var map = result.course_map || [];
    if (map.length) {
      html += '<h3 class="sec">Course map</h3><table><thead><tr><th>Week</th><th>Topics</th>' +
              '<th>Assessments due</th><th>Flags</th></tr></thead><tbody>';
      map.forEach(function (row) {
        var flagged = (row.flags || []).length > 0;
        html += '<tr class="' + (flagged ? "flag" : "") + '"><td>' + row.week + '</td><td>' +
                (row.topics.length ? esc(row.topics.join("; ")) : '<span class="chip warn">no topic</span>') +
                '</td><td>' +
                (row.assessments.length
                  ? row.assessments.map(function (a) { return esc(a.name) + " (" + a.weight + "%)"; }).join("; ")
                  : "-") +
                '</td><td>' + (row.flags || []).map(function (f) {
                  return '<span class="chip">' + esc(f.replace(/_/g, " ")) + '</span>'; }).join("") + '</td></tr>';
      });
      html += '</tbody></table>';
    }

    if (result.syllabus) {
      html += '<h3 class="sec">Generated syllabus draft</h3><pre class="syllabus">' +
              esc(result.syllabus) + '</pre>';
    }

    $("#results").innerHTML = html;
  }

  function payload() {
    return { brief: $("#brief").value, profile: $("#profileSelect").value };
  }

  function analyze() {
    var body = payload();
    if (!body.brief.trim()) { toast("Paste a brief first"); return; }
    setStatus("reviewing...");
    fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) { return r.json(); }).then(function (data) {
      if (data.error) { setStatus("error"); toast(data.error); return; }
      setStatus("scored " + data.score.overall);
      render(data);
    }).catch(function (err) { setStatus("error"); toast(String(err)); });
  }

  function exportAs(fmt) {
    var body = payload();
    if (!body.brief.trim()) { toast("Paste a brief first"); return; }
    body.format = fmt;
    fetch("/api/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) { return r.blob(); }).then(function (blob) {
      var url = URL.createObjectURL(blob);
      var link = document.createElement("a");
      link.href = url;
      link.download = "syllabus-review." + fmt;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      toast("Exported " + fmt.toUpperCase());
    }).catch(function (err) { toast(String(err)); });
  }

  function loadRuns() {
    fetch("/api/runs").then(function (r) { return r.json(); }).then(function (data) {
      state.runs = data.runs || [];
      $("#runCount").textContent = state.runs.length;
      var html = "";
      state.runs.forEach(function (run) {
        html += '<div class="run-item"><div><div>' + esc(run.title) + '</div>' +
                '<div class="meta-line">' + esc(run.created_at) + '</div></div>' +
                '<span class="score">' + run.score + '</span>' +
                '<button data-load="' + run.id + '">open</button>' +
                '<button data-del="' + run.id + '">del</button></div>';
      });
      $("#runList").innerHTML = html || '<div class="meta-line">No saved runs yet.</div>';
    });
  }

  document.addEventListener("click", function (event) {
    var target = event.target;
    if (target.dataset && target.dataset.load) {
      fetch("/api/runs/" + target.dataset.load).then(function (r) { return r.json(); })
        .then(function (run) {
          $("#brief").value = run.brief;
          $("#profileSelect").value = run.profile;
          render(run.result);
          setStatus("loaded run #" + run.id);
        });
    }
    if (target.dataset && target.dataset.del) {
      fetch("/api/runs/" + target.dataset.del, { method: "DELETE" }).then(loadRuns);
    }
  });

  $("#analyzeBtn").addEventListener("click", analyze);
  $("#saveBtn").addEventListener("click", function () {
    var body = payload();
    if (!body.brief.trim()) { toast("Paste a brief first"); return; }
    fetch("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) { return r.json(); }).then(function (data) {
      if (data.error) { toast(data.error); return; }
      toast("Saved run #" + data.id);
      loadRuns();
    });
  });
  $("#mdBtn").addEventListener("click", function () { exportAs("md"); });
  $("#csvBtn").addEventListener("click", function () { exportAs("csv"); });
  $("#jsonBtn").addEventListener("click", function () { exportAs("json"); });

  $("#sampleSelect").addEventListener("change", function () {
    var id = $("#sampleSelect").value;
    if (!id) return;
    state.samples.forEach(function (sample) {
      if (sample.id === id) { $("#brief").value = sample.brief; analyze(); }
    });
  });

  fetch("/api/samples").then(function (r) { return r.json(); }).then(function (data) {
    state.samples = data.samples || [];
    var select = $("#sampleSelect");
    state.samples.forEach(function (sample) {
      var option = document.createElement("option");
      option.value = sample.id;
      option.textContent = sample.title;
      select.appendChild(option);
    });
  });

  fetch("/api/health").then(function (r) { return r.json(); }).then(function (data) {
    var select = $("#profileSelect");
    (data.profiles || []).forEach(function (profile) {
      var option = document.createElement("option");
      option.value = profile;
      option.textContent = profile.replace(/_/g, " ");
      select.appendChild(option);
    });
    select.value = "general";
    setStatus("ready");
  });

  loadRuns();
})();
