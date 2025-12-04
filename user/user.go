package user

import (
	"errors"
	"time"

	"golang.org/x/crypto/bcrypt"
)

// User 表示系统中的用户
type User struct {
	ID           string    `json:"id" bson:"_id"`
	Username     string    `json:"username" bson:"username"`
	Email        string    `json:"email" bson:"email"`
	PasswordHash string    `json:"-" bson:"password_hash"` // 不在 JSON 中暴露密码
	CreatedAt    time.Time `json:"created_at" bson:"created_at"`
	UpdatedAt    time.Time `json:"updated_at" bson:"updated_at"`
}

// 定义错误
var (
	ErrInvalidCredentials = errors.New("invalid username or password")
	ErrUserExists         = errors.New("user already exists")
	ErrUserNotFound       = errors.New("user not found")
	ErrWeakPassword       = errors.New("password is too weak")
)

// HashPassword 使用 bcrypt 哈希密码
func HashPassword(password string) (string, error) {
	// 检查密码强度
	if len(password) < 6 {
		return "", ErrWeakPassword
	}

	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(bytes), nil
}

// CheckPassword 验证密码是否匹配
func CheckPassword(hashedPassword, password string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(password))
	return err == nil
}

// PublicUser 返回用户的公开信息（不包含敏感数据）
type PublicUser struct {
	ID        string    `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	CreatedAt time.Time `json:"created_at"`
}

// ToPublic 将 User 转换为 PublicUser
func (u *User) ToPublic() PublicUser {
	return PublicUser{
		ID:        u.ID,
		Username:  u.Username,
		Email:     u.Email,
		CreatedAt: u.CreatedAt,
	}
}

