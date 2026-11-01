
const http = require("http");
const fs = require("fs");
const path = require("path");

const PORT = process.env.PORT || 10000;

const server = http.createServer((req, res) => {

    // UptimeRobot health-check endpoint
    if (req.url === "/ping") {
        res.writeHead(200, {
            "Content-Type": "text/plain"
        });
        return res.end("pong");
    }

    // Serve the HTML website
    const filePath = path.join(
        __dirname,
        "index.html"
    );

    fs.readFile(filePath, (err, data) => {
        if (err) {
            res.writeHead(500);
            return res.end("Server error");
        }

        res.writeHead(200, {
            "Content-Type": "text/html"
        });

        res.end(data);
    });

});

server.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on port ${PORT}`);
});
