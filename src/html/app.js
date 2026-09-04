/* Miflaga front end: fetch a party name from the server and reveal it on a
 * ballot slip, over a waving Israeli flag drawn on a canvas. */
(function () {
	"use strict";

	var ballot = document.getElementById("ballot");
	var lettersEl = document.getElementById("letters");
	var nounEl = document.getElementById("noun");
	var adjectiveEl = document.getElementById("adjective");
	var statusEl = document.getElementById("status");
	var generateButton = document.getElementById("generate");
	var copyButton = document.getElementById("copy");
	var shareButton = document.getElementById("share");
	var current = null;

	/* Remove and re-add a class so its CSS animation plays again. */
	function replay(el, cls) {
		el.classList.remove(cls);
		el.getBoundingClientRect();
		el.classList.add(cls);
	}

	function show(party) {
		current = party;
		ballot.classList.remove("shown");
		lettersEl.textContent = party.letters;
		nounEl.textContent = party.noun;
		adjectiveEl.textContent = party.adjective;
		replay(ballot, "drop");
		window.requestAnimationFrame(function () {
			window.requestAnimationFrame(function () {
				ballot.classList.add("shown");
			});
		});
		statusEl.textContent = "";
	}

	function generate() {
		generateButton.disabled = true;
		fetch("/app/name", { cache: "no-store" })
			.then(function (response) {
				if (!response.ok) {
					throw new Error("HTTP " + response.status);
				}
				return response.json();
			})
			.then(show)
			.catch(function () {
				statusEl.textContent = "משהו השתבש. כמו בקואליציה. נסו שוב.";
			})
			.then(function () {
				generateButton.disabled = false;
			});
	}

	function copyName() {
		if (!current) {
			return;
		}
		navigator.clipboard.writeText(current.name).then(function () {
			statusEl.textContent = "השם הועתק. עכשיו רק צריך 3.25% מהקולות.";
		}, function () {
			statusEl.textContent = "ההעתקה נכשלה, אבל אפשר להעתיק ידנית.";
		});
	}

	function shareName() {
		if (!current) {
			return;
		}
		navigator.share({
			title: current.name,
			text: "המפלגה החדשה שלי: " + current.name,
			url: window.location.href
		}).catch(function () {
			/* the user closed the share sheet; nothing to report */
		});
	}

	/* ---- waving flag background ------------------------------------- */

	var FLAG_WIDTH = 1100;
	var FLAG_HEIGHT = 800;

	/* Draw the flag of Israel into a context of the given size: two blue
	 * stripes and a Star of David, following the official proportions. */
	function drawFlag(ctx, width, height) {
		var unit = height / 160;
		var cx = width / 2;
		var cy = height / 2;
		var radius = 37 * unit;
		ctx.fillStyle = "#ffffff";
		ctx.fillRect(0, 0, width, height);
		ctx.fillStyle = "#0038b8";
		ctx.fillRect(0, 15 * unit, width, 25 * unit);
		ctx.fillRect(0, 120 * unit, width, 25 * unit);
		ctx.strokeStyle = "#0038b8";
		ctx.lineWidth = 5.5 * unit;
		ctx.lineJoin = "miter";
		[-90, 90].forEach(function (startDegrees) {
			ctx.beginPath();
			for (var i = 0; i < 3; i++) {
				var angle = (startDegrees + i * 120) * Math.PI / 180;
				var x = cx + radius * Math.cos(angle);
				var y = cy + radius * Math.sin(angle);
				if (i === 0) {
					ctx.moveTo(x, y);
				} else {
					ctx.lineTo(x, y);
				}
			}
			ctx.closePath();
			ctx.stroke();
		});
	}

	function startFlag(canvas) {
		var ctx = canvas.getContext("2d");
		var flag = document.createElement("canvas");
		flag.width = FLAG_WIDTH;
		flag.height = FLAG_HEIGHT;
		drawFlag(flag.getContext("2d"), FLAG_WIDTH, FLAG_HEIGHT);

		var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
		var time = 0;

		function resize() {
			canvas.width = window.innerWidth;
			canvas.height = window.innerHeight;
		}

		function frame() {
			var width = canvas.width;
			var height = canvas.height;
			var amplitude = Math.min(height, width) * 0.035;
			/* cover the viewport, leaving room for the wave */
			var scale = Math.max(width / FLAG_WIDTH, (height - 2 * amplitude) / FLAG_HEIGHT);
			var drawWidth = FLAG_WIDTH * scale;
			var drawHeight = FLAG_HEIGHT * scale;
			var x0 = (width - drawWidth) / 2;
			var y0 = (height - drawHeight) / 2;
			var slice = 6;
			ctx.clearRect(0, 0, width, height);
			for (var x = 0; x < drawWidth; x += slice) {
				var progress = x / drawWidth;
				/* the pole is on the right (reading direction), so the wave
				 * grows toward the left edge */
				var envelope = 0.25 + 0.75 * (1 - progress);
				var offset = Math.sin(progress * 3.5 * Math.PI - time) * amplitude * envelope;
				ctx.drawImage(
					flag,
					x / scale, 0, slice / scale, FLAG_HEIGHT,
					x0 + x, y0 + offset, slice, drawHeight
				);
			}
			time += 0.045;
		}

		function loop() {
			frame();
			window.requestAnimationFrame(loop);
		}

		window.addEventListener("resize", function () {
			resize();
			if (reduceMotion) {
				frame();
			}
		});
		resize();
		if (reduceMotion) {
			frame();
		} else {
			loop();
		}
	}

	/* ---- wiring ----------------------------------------------------- */

	generateButton.addEventListener("click", generate);
	copyButton.addEventListener("click", copyName);
	if (navigator.share) {
		shareButton.hidden = false;
		shareButton.addEventListener("click", shareName);
	}
	document.addEventListener("keydown", function (event) {
		if (event.key === " " && event.target === document.body) {
			event.preventDefault();
			generate();
		}
	});

	startFlag(document.getElementById("flag"));
	generate();
}());
