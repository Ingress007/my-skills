package com.example.user.service;

import com.example.common.dto.UserDTO;
import com.example.user.dao.UserMapper;
import com.example.user.entity.User;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class UserService {

    @Autowired
    private UserMapper userMapper;

    public List<UserDTO> listAll() {
        return userMapper.selectList(null).stream()
                .map(this::toDTO)
                .collect(Collectors.toList());
    }

    public UserDTO getById(Long id) {
        User user = userMapper.selectById(id);
        return user != null ? toDTO(user) : null;
    }

    public UserDTO create(UserDTO dto) {
        User user = new User(dto.getName(), dto.getEmail());
        userMapper.insert(user);
        return toDTO(user);
    }

    private UserDTO toDTO(User user) {
        UserDTO dto = new UserDTO();
        dto.setId(user.getId());
        dto.setName(user.getName());
        dto.setEmail(user.getEmail());
        dto.setCreatedAt(user.getCreatedAt());
        return dto;
    }
}