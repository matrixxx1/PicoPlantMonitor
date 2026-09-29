package main

import (
	"errors"
	"flag"
	"log"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"path/filepath"
	"time"

	"tailscale.com/tsnet"
)

func main() {
	backend := flag.String("backend", "", "Pico LAN URL (required)")
	stateDir := flag.String("state-dir", "", "persistent Tailscale node state directory")
	logFile := flag.String("log-file", "", "optional log file for background operation")
	flag.Parse()
	if *stateDir == "" {
		*stateDir = filepath.Join(os.Getenv("LOCALAPPDATA"), "PicoPlantMonitor", "tailnet-state")
	}
	if err := os.MkdirAll(*stateDir, 0700); err != nil {
		log.Fatal(err)
	}
	if *logFile != "" {
		file, err := os.OpenFile(*logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
		if err != nil {
			log.Fatal(err)
		}
		defer file.Close()
		log.SetOutput(file)
	}
	target, err := url.Parse(*backend)
	if err != nil || target.Scheme != "http" || target.Host == "" {
		log.Fatal("backend must be an HTTP URL")
	}
	proxy := httputil.NewSingleHostReverseProxy(target)
	proxy.Transport = &http.Transport{
		DialContext:         (&net.Dialer{Timeout: 5 * time.Second}).DialContext,
		ResponseHeaderTimeout: 10 * time.Second,
		IdleConnTimeout:     30 * time.Second,
	}
	proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		log.Printf("Pico unavailable: %v", err)
		http.Error(w, "Pico is offline on the local network", http.StatusBadGateway)
	}
	server := &tsnet.Server{Hostname: "PicoPlantMonitor", Dir: *stateDir}
	defer server.Close()
	listener, err := server.Listen("tcp", ":80")
	if err != nil {
		log.Fatal(err)
	}
	defer listener.Close()
	log.Printf("PicoPlantMonitor tailnet proxy ready; backend %s", target.String())
	httpServer := &http.Server{Handler: proxy, ReadHeaderTimeout: 5 * time.Second}
	if err := httpServer.Serve(listener); err != nil && !errors.Is(err, http.ErrServerClosed) {
		log.Fatal(err)
	}
}
