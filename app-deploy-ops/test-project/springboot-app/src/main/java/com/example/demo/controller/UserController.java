package com.example.demo.controller;

import com.example.demo.entity.User;
import com.example.demo.dao.UserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.concurrent.TimeUnit;

@RestController
@RequestMapping("/api")
public class UserController {

    @Autowired
    private UserMapper userMapper;

    @Autowired(required = false)
    private StringRedisTemplate redisTemplate;

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }

    @GetMapping("/users")
    public List<User> getUsers() {
        return userMapper.selectList(null);
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        User user = userMapper.selectById(id);
        return user != null
                ? ResponseEntity.ok(user)
                : ResponseEntity.notFound().build();
    }

    @PostMapping("/users")
    public User createUser(@RequestBody User user) {
        userMapper.insert(user);
        return user;
    }

    @GetMapping("/cache/{key}")
    public ResponseEntity<String> getCache(@PathVariable String key) {
        if (redisTemplate == null) {
            return ResponseEntity.ok("Redis not configured");
        }
        String value = redisTemplate.opsForValue().get(key);
        return value != null
                ? ResponseEntity.ok(value)
                : ResponseEntity.notFound().build();
    }

    @PostMapping("/cache/{key}")
    public ResponseEntity<String> setCache(@PathVariable String key,
                                            @RequestBody String value) {
        if (redisTemplate == null) {
            return ResponseEntity.ok("Redis not configured");
        }
        redisTemplate.opsForValue().set(key, value, 60, TimeUnit.SECONDS);
        return ResponseEntity.ok("OK");
    }
}