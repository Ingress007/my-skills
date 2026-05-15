package com.example.pay.dao;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.pay.entity.PayRecord;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface PayRecordMapper extends BaseMapper<PayRecord> {
}