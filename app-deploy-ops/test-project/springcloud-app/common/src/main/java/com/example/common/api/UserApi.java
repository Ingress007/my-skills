package com.example.common.api;

import com.example.common.dto.UserDTO;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RequestMapping("/api/users")
public interface UserApi {

    @GetMapping
    List<UserDTO> list();

    @GetMapping("/{id}")
    UserDTO getById(@PathVariable("id") Long id);

    @PostMapping
    UserDTO create(@RequestBody UserDTO user);
}