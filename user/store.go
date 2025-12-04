package user

import (
	"context"
	"errors"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
)

// Store 定义用户存储接口
type Store interface {
	CreateUser(user *User) error
	GetUserByID(id string) (*User, error)
	GetUserByUsername(username string) (*User, error)
	GetUserByEmail(email string) (*User, error)
	UpdateUser(user *User) error
}

// MongoUserStore 是 Store 接口的 MongoDB 实现
type MongoUserStore struct {
	collection *mongo.Collection
}

// NewMongoUserStore 创建一个新的 MongoDB 用户存储实例
func NewMongoUserStore(collection *mongo.Collection) *MongoUserStore {
	return &MongoUserStore{
		collection: collection,
	}
}

// CreateUser 创建新用户
func (s *MongoUserStore) CreateUser(user *User) error {
	// 检查用户名是否已存在
	existing, _ := s.GetUserByUsername(user.Username)
	if existing != nil {
		return ErrUserExists
	}

	// 检查邮箱是否已存在
	existing, _ = s.GetUserByEmail(user.Email)
	if existing != nil {
		return ErrUserExists
	}

	// 设置时间戳
	now := time.Now()
	user.CreatedAt = now
	user.UpdatedAt = now

	_, err := s.collection.InsertOne(context.TODO(), user)
	return err
}

// GetUserByID 根据 ID 获取用户
func (s *MongoUserStore) GetUserByID(id string) (*User, error) {
	var user User
	filter := bson.M{"_id": id}

	err := s.collection.FindOne(context.TODO(), filter).Decode(&user)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, ErrUserNotFound
		}
		return nil, err
	}

	return &user, nil
}

// GetUserByUsername 根据用户名获取用户
func (s *MongoUserStore) GetUserByUsername(username string) (*User, error) {
	var user User
	filter := bson.M{"username": username}

	err := s.collection.FindOne(context.TODO(), filter).Decode(&user)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, ErrUserNotFound
		}
		return nil, err
	}

	return &user, nil
}

// GetUserByEmail 根据邮箱获取用户
func (s *MongoUserStore) GetUserByEmail(email string) (*User, error) {
	var user User
	filter := bson.M{"email": email}

	err := s.collection.FindOne(context.TODO(), filter).Decode(&user)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, ErrUserNotFound
		}
		return nil, err
	}

	return &user, nil
}

// UpdateUser 更新用户信息
func (s *MongoUserStore) UpdateUser(user *User) error {
	user.UpdatedAt = time.Now()

	filter := bson.M{"_id": user.ID}
	update := bson.M{"$set": user}

	result, err := s.collection.UpdateOne(context.TODO(), filter, update)
	if err != nil {
		return err
	}

	if result.MatchedCount == 0 {
		return ErrUserNotFound
	}

	return nil
}

