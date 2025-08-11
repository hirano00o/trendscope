package scheduler

import (
	"context"
	"fmt"
	"log"
	"time"
)

// Job represents a scheduled job
//
// @description スケジュールされたジョブを表現する構造体
// 実行すべき処理とその設定を含む
//
// @example
// ```go
//
//	job := &Job{
//	    Name: "stock-analysis",
//	    Handler: func(ctx context.Context) error {
//	        return analyzeStocks(ctx)
//	    },
//	}
//
// ```
type Job struct {
	// Name is the job identifier
	Name string
	// Handler is the function to execute
	Handler func(context.Context) error
}

// Scheduler represents a cron scheduler
//
// @description Cronスケジューラー
// 指定された時間に定期的にジョブを実行する
// シンプルなクロン機能を提供（外部ライブラリなし）
//
// @example
// ```go
// scheduler := NewScheduler()
// scheduler.AddJob("0 10 * * 1-5", job) // 平日10時
// scheduler.Start(ctx)
// ```
type Scheduler struct {
	// jobs is a map of cron expressions to jobs
	jobs map[string]*Job
	// running indicates if the scheduler is running
	running bool
	// ctx is the context for the scheduler
	ctx context.Context
	// cancel is the cancel function for the scheduler
	cancel context.CancelFunc
}

// NewScheduler creates a new cron scheduler
//
// @description 新しいCronスケジューラーを作成する
// ジョブ管理とスケジュール実行機能を提供
//
// @returns {*Scheduler} 設定済みのスケジューラーインスタンス
//
// @example
// ```go
// scheduler := NewScheduler()
// defer scheduler.Stop()
// ```
func NewScheduler() *Scheduler {
	return &Scheduler{
		jobs: make(map[string]*Job),
	}
}

// AddJob adds a job to the scheduler with the specified cron expression
//
// @description 指定されたCron式でジョブをスケジューラーに追加する
//
// サポートするCron形式：
// - "分 時 日 月 曜日" （例: "0 10 * * 1-5" = 平日10時）
// - 曜日: 0=日曜日, 1=月曜日, ..., 6=土曜日
// - 範囲: 1-5 (月曜日から金曜日)
//
// @param {string} cronExpr Cron式（例："0 10 * * 1-5"）
// @param {*Job} job 実行するジョブ
// @throws {error} 無効なCron式の場合
//
// @example
// ```go
//
//	job := &Job{
//	    Name: "daily-analysis",
//	    Handler: analyzeStocksHandler,
//	}
//
// err := scheduler.AddJob("0 10 * * 1-5", job)
//
//	if err != nil {
//	    log.Fatal(err)
//	}
//
// ```
func (s *Scheduler) AddJob(cronExpr string, job *Job) error {
	// Basic validation of cron expression
	if err := s.validateCronExpression(cronExpr); err != nil {
		return fmt.Errorf("invalid cron expression '%s': %w", cronExpr, err)
	}

	s.jobs[cronExpr] = job
	log.Printf("Added job '%s' with schedule '%s'", job.Name, cronExpr)
	return nil
}

// Start starts the scheduler
//
// @description スケジューラーを開始する
// バックグラウンドでジョブのスケジュール監視を開始
// コンテキストがキャンセルされるまで実行を継続
//
// @param {context.Context} ctx スケジューラーのコンテキスト
//
// @example
// ```go
// ctx := context.Background()
// go scheduler.Start(ctx) // バックグラウンドで開始
//
// // メインプロセスの処理...
//
// scheduler.Stop() // 終了時
// ```
func (s *Scheduler) Start(ctx context.Context) {
	if s.running {
		log.Printf("Scheduler is already running")
		return
	}

	s.ctx, s.cancel = context.WithCancel(ctx)
	s.running = true

	log.Printf("Starting scheduler with %d jobs", len(s.jobs))

	// Main scheduler loop
	ticker := time.NewTicker(1 * time.Minute) // Check every minute
	defer ticker.Stop()

	for {
		select {
		case now := <-ticker.C:
			s.checkAndRunJobs(now)
		case <-s.ctx.Done():
			log.Printf("Scheduler stopped")
			return
		}
	}
}

// Stop stops the scheduler
//
// @description スケジューラーを停止する
// 実行中のジョブの完了を待たずに即座に停止
//
// @example
// ```go
// scheduler.Stop()
// ```
func (s *Scheduler) Stop() {
	if !s.running {
		return
	}

	log.Printf("Stopping scheduler...")
	s.cancel()
	s.running = false
}

// checkAndRunJobs checks if any jobs should be run at the given time
//
// @description 指定された時刻に実行すべきジョブがあるかチェックし、実行する
// 各ジョブのCron式を評価し、条件に一致する場合は実行
//
// @param {time.Time} now 現在の時刻
func (s *Scheduler) checkAndRunJobs(now time.Time) {
	for cronExpr, job := range s.jobs {
		if s.shouldRunJob(cronExpr, now) {
			log.Printf("Running job '%s' at %s", job.Name, now.Format("2006-01-02 15:04:05"))

			// Run job in a separate goroutine
			go func(j *Job) {
				ctx, cancel := context.WithTimeout(context.Background(), 30*time.Minute)
				defer cancel()

				start := time.Now()
				if err := j.Handler(ctx); err != nil {
					log.Printf("Job '%s' failed: %v [%v]", j.Name, err, time.Since(start))
				} else {
					log.Printf("Job '%s' completed successfully [%v]", j.Name, time.Since(start))
				}
			}(job)
		}
	}
}

// shouldRunJob determines if a job should run based on the cron expression and current time
//
// @description Cron式と現在時刻に基づいて、ジョブを実行すべきかどうかを判定する
// シンプルなCron式のサポート：分、時、日、月、曜日
//
// @param {string} cronExpr Cron式
// @param {time.Time} now 現在時刻
// @returns {bool} ジョブを実行すべきかどうか
func (s *Scheduler) shouldRunJob(cronExpr string, now time.Time) bool {
	// Simple cron parsing for the most common case: "0 10 * * 1-5" (weekdays at 10:00)
	// This is a simplified implementation for demonstration

	// Parse the cron expression
	parts, err := s.parseCronExpression(cronExpr)
	if err != nil {
		log.Printf("Error parsing cron expression '%s': %v", cronExpr, err)
		return false
	}

	minute, hour, day, month, weekday := parts[0], parts[1], parts[2], parts[3], parts[4]

	// Check minute
	if minute != "*" && minute != fmt.Sprintf("%d", now.Minute()) {
		return false
	}

	// Check hour
	if hour != "*" && hour != fmt.Sprintf("%d", now.Hour()) {
		return false
	}

	// Check day
	if day != "*" && day != fmt.Sprintf("%d", now.Day()) {
		return false
	}

	// Check month
	if month != "*" && month != fmt.Sprintf("%d", int(now.Month())) {
		return false
	}

	// Check weekday (0=Sunday, 1=Monday, ..., 6=Saturday)
	if weekday != "*" {
		currentWeekday := int(now.Weekday())
		if !s.matchesWeekdayRange(weekday, currentWeekday) {
			return false
		}
	}

	return true
}

// validateCronExpression validates a cron expression format
//
// @description Cron式のフォーマットを検証する
// 5つのフィールド（分 時 日 月 曜日）が存在することを確認
//
// @param {string} cronExpr 検証するCron式
// @throws {error} 無効な形式の場合
func (s *Scheduler) validateCronExpression(cronExpr string) error {
	parts, err := s.parseCronExpression(cronExpr)
	if err != nil {
		return err
	}

	if len(parts) != 5 {
		return fmt.Errorf("cron expression must have 5 fields, got %d", len(parts))
	}

	return nil
}

// parseCronExpression parses a cron expression into its components
//
// @description Cron式を構成要素に分解する
// スペースで分割して各フィールドを取得
//
// @param {string} cronExpr パースするCron式
// @returns {[]string} Cron式の構成要素のスライス
// @throws {error} パースに失敗した場合
func (s *Scheduler) parseCronExpression(cronExpr string) ([]string, error) {
	parts := make([]string, 0)
	currentPart := ""

	for _, char := range cronExpr {
		if char == ' ' {
			if currentPart != "" {
				parts = append(parts, currentPart)
				currentPart = ""
			}
		} else {
			currentPart += string(char)
		}
	}

	// Add the last part
	if currentPart != "" {
		parts = append(parts, currentPart)
	}

	return parts, nil
}

// matchesWeekdayRange checks if the current weekday matches the cron weekday specification
//
// @description 現在の曜日がCron式の曜日指定と一致するかチェックする
// 範囲指定（例：1-5）をサポート
//
// @param {string} weekdaySpec 曜日指定（例："1-5", "1", "*"）
// @param {int} currentWeekday 現在の曜日（0=日曜日）
// @returns {bool} 一致するかどうか
func (s *Scheduler) matchesWeekdayRange(weekdaySpec string, currentWeekday int) bool {
	if weekdaySpec == "*" {
		return true
	}

	// Check for range (e.g., "1-5")
	if len(weekdaySpec) >= 3 && weekdaySpec[1] == '-' {
		start := int(weekdaySpec[0] - '0')
		end := int(weekdaySpec[2] - '0')

		return currentWeekday >= start && currentWeekday <= end
	}

	// Check for exact match
	if len(weekdaySpec) == 1 {
		specified := int(weekdaySpec[0] - '0')
		return currentWeekday == specified
	}

	return false
}

// IsRunning returns whether the scheduler is currently running
//
// @description スケジューラーが現在実行中かどうかを返す
//
// @returns {bool} 実行中かどうか
func (s *Scheduler) IsRunning() bool {
	return s.running
}

// JobCount returns the number of jobs in the scheduler
//
// @description スケジューラーに登録されているジョブ数を返す
//
// @returns {int} ジョブ数
func (s *Scheduler) JobCount() int {
	return len(s.jobs)
}

// GetNextExecutionTime calculates the next execution time based on a cron expression
//
// @description Cron式に基づいて次回実行時刻を計算する
// 現在時刻から最も近い次の実行時刻を返す
//
// サポートするCron形式：
// - "分 時 日 月 曜日" （例: "0 10 * * 1-5" = 平日10時）
// - 曜日: 0=日曜日, 1=月曜日, ..., 6=土曜日
// - 範囲: 1-5 (月曜日から金曜日)
// - ワイルドカード: * (すべての値)
//
// @param {string} cronExpr Cron式（例："0 10 * * 1-5"）
// @returns {time.Time} 次回実行予定時刻
// @throws {error} 無効なCron式の場合
//
// @example
// ```go
// nextTime, err := GetNextExecutionTime("0 10 * * 1-5")
// if err != nil {
//     log.Printf("Error: %v", err)
// } else {
//     log.Printf("Next execution: %s", nextTime.Format("2006-01-02 15:04:05"))
// }
// ```
func GetNextExecutionTime(cronExpr string) (time.Time, error) {
	// Create a temporary scheduler for validation
	tempScheduler := NewScheduler()
	if err := tempScheduler.validateCronExpression(cronExpr); err != nil {
		return time.Time{}, fmt.Errorf("invalid cron expression '%s': %w", cronExpr, err)
	}

	// Parse the cron expression
	parts, err := tempScheduler.parseCronExpression(cronExpr)
	if err != nil {
		return time.Time{}, fmt.Errorf("failed to parse cron expression '%s': %w", cronExpr, err)
	}

	return tempScheduler.calculateNextExecution(parts, time.Now())
}

// calculateNextExecution calculates the next execution time from current time
//
// @description 現在時刻から次回実行時刻を計算する内部関数
// 
// @param {[]string} cronParts パース済みのCron式の各部分
// @param {time.Time} from 計算の基準時刻
// @returns {time.Time} 次回実行予定時刻
// @throws {error} 計算に失敗した場合
func (s *Scheduler) calculateNextExecution(cronParts []string, from time.Time) (time.Time, error) {
	if len(cronParts) != 5 {
		return time.Time{}, fmt.Errorf("cron expression must have 5 fields, got %d", len(cronParts))
	}

	minute, hour, day, month, weekday := cronParts[0], cronParts[1], cronParts[2], cronParts[3], cronParts[4]

	// Start from the next minute
	next := time.Date(from.Year(), from.Month(), from.Day(), from.Hour(), from.Minute()+1, 0, 0, from.Location())

	// Try to find the next execution time within the next year
	for attempts := 0; attempts < 365*24*60; attempts++ {
		// Check if this time matches the cron expression
		if s.matchesCronExpression(next, minute, hour, day, month, weekday) {
			return next, nil
		}
		next = next.Add(1 * time.Minute)
	}

	return time.Time{}, fmt.Errorf("could not find next execution time within one year")
}

// matchesCronExpression checks if a given time matches the cron expression components
//
// @description 指定された時刻がCron式の各コンポーネントと一致するかチェック
//
// @param {time.Time} t チェック対象の時刻
// @param {string} minute 分の指定
// @param {string} hour 時の指定  
// @param {string} day 日の指定
// @param {string} month 月の指定
// @param {string} weekday 曜日の指定
// @returns {bool} 一致するかどうか
func (s *Scheduler) matchesCronExpression(t time.Time, minute, hour, day, month, weekday string) bool {
	// Check minute
	if minute != "*" && !s.matchesNumericValue(minute, t.Minute()) {
		return false
	}

	// Check hour
	if hour != "*" && !s.matchesNumericValue(hour, t.Hour()) {
		return false
	}

	// Check day
	if day != "*" && !s.matchesNumericValue(day, t.Day()) {
		return false
	}

	// Check month
	if month != "*" && !s.matchesNumericValue(month, int(t.Month())) {
		return false
	}

	// Check weekday (0=Sunday, 1=Monday, ..., 6=Saturday)
	if weekday != "*" {
		currentWeekday := int(t.Weekday())
		if !s.matchesWeekdayRange(weekday, currentWeekday) {
			return false
		}
	}

	return true
}

// matchesNumericValue checks if a numeric value matches a cron field specification
//
// @description 数値がCronフィールドの指定と一致するかチェック
//
// @param {string} spec Cronフィールドの指定（例："10", "*"）
// @param {int} value チェック対象の値
// @returns {bool} 一致するかどうか
func (s *Scheduler) matchesNumericValue(spec string, value int) bool {
	if spec == "*" {
		return true
	}

	// Check for exact match
	if spec == fmt.Sprintf("%d", value) {
		return true
	}

	// TODO: Add support for ranges (e.g., "10-15") and lists (e.g., "10,12,14") if needed
	
	return false
}
