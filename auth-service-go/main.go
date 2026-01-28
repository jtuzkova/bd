package main

import (
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"time"
	_ "github.com/go-sql-driver/mysql"
)

var db *sql.DB 

type Response struct {
	User struct {
		Ex_id   int    `json:"ex_id"`
		Role    string `json:"role"`
		Pass_id int    `json:"pass_id"`
	} `json:"user"`
}

func mainHandle(w http.ResponseWriter, r *http.Request) {
	var resp Response

	log.Printf("[%s] %s %s", time.Now().Format("15:04:05"), r.Method, r.URL.Path)
	log.Printf("  Headers: %v", r.Header)
	
	w.Header().Set("Content-Type", "application/json")
	
	user, pass, ok := r.BasicAuth()
	if !ok || user == "" || pass == "" {
		log.Printf("  ERROR: Bad auth - user: '%s', pass provided: %v", user, pass != "")
		w.WriteHeader(400)
		jsonData, _ := json.Marshal(map[string]string{"error": "Bad request"})
		w.Write(jsonData)
		return
	}
	
	log.Printf("  Auth attempt - user: '%s'", user)
	
	err := db.QueryRow(
		"SELECT ex_id, role, pass_id FROM external_users WHERE login = ? AND passw = ?",
		user, pass,
	).Scan(&resp.User.Ex_id, &resp.User.Role, &resp.User.Pass_id)
	
	if err != nil {
		if err == sql.ErrNoRows {
			log.Printf("  ERROR: User not found in database")
		} else {
			log.Printf("  ERROR: Database query failed: %v", err)
		}
		w.WriteHeader(401)
		jsonData, _ := json.Marshal(map[string]string{"error": "User not found"})
		w.Write(jsonData)
		return
	}
	log.Printf("  SUCCESS: User found - ex_id: %d, role: %s, pass_id: %d", resp.User.Ex_id, resp.User.Role, resp.User.Pass_id)
	
	jsonData, _ := json.Marshal(resp)
	w.Write(jsonData)
}

func main() {
	log.Println("Starting server...")
	
	connStr := "root:@tcp(127.0.0.1)/new_schema"
	
	var err error
	db, err = sql.Open("mysql", connStr)
	if err != nil {
		log.Fatalf("ERROR: Failed to open database: %v", err)
	}
	defer db.Close()
	
	if err := db.Ping(); err != nil {
		log.Fatalf("ERROR: Database ping failed: %v", err)
	}
	log.Printf("Database (%s) connection successful!", connStr)
	
	log.Println("Starting HTTP server on port 5002...")
	http.HandleFunc("/", mainHandle)
	
	log.Println("Server is ready!")
	
	if err := http.ListenAndServe(":5002", nil); err != nil {
		log.Fatalf("ERROR: Server failed: %v", err)
	}
}